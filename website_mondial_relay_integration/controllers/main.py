from odoo.addons.website_mondial_relay_integration.controllers.mondial_relay_response import Response
from odoo import fields, http, tools, _
from odoo.http import request
import logging
import requests
import base64
import hashlib
import xml.etree.ElementTree as etree

_logger = logging.getLogger('Ecommerce Mondial Relay')
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleDelivery(WebsiteSale):
    @http.route()
    def update_eshop_carrier(self, **post):
        result = super(WebsiteSaleDelivery, self).update_eshop_carrier(**post)
        order = request.website.sale_get_order()
        if order:
            order.carrier_id = result.get('carrier_id')
        return result


class WebsiteSale(http.Controller):

    @http.route(['/mondial_relay_service'], type='json', auth='public', methods=['POST'], website=True, csrf=False)
    def mondial_relay_service(self, **post):
        results = {}
        if post.get('order') and post.get('delivery_type'):
            delivery_method = request.env['delivery.carrier'].sudo().browse(int(post.get('delivery_type')))
            if delivery_method.delivery_type == 'mondial_relay_vts':
                results = request.env['ir.ui.view']._render_template(
                    'website_mondial_relay_integration.mondial_relay_shipping_location')
            order = request.website.sale_get_order()
            if order and order.carrier_id:
                existing_records = request.env['mondialrelay.locations'].sudo().search([('sale_order_id', '=', order.id)])
                existing_records.sudo().unlink()
        return results

    @http.route(['/mondial_relay_get_location'], type='json', auth='public', methods=['POST'],
                website=True, csrf=False)
    def mondial_relay_get_location(self, **post):
        order = request.website.sale_get_order()
        # Shipper and Recipient Address
        shipper_address = order.warehouse_id.partner_id
        recipient_address = order.partner_shipping_id
        # check sender Address
        if not shipper_address.zip or not shipper_address.city or not shipper_address.country_id:
            return {'error': 'Please Define Proper Sender Address!'}
        # check Receiver Address
        if not recipient_address.zip or not recipient_address.city or not recipient_address.country_id:
            return {'error': 'Please Define Proper Recipient Address!'}
        if not order.company_id.mondial_relay_merchant_code and order.company_id.mondial_relay_security_code:
            return {'error': 'Credential not available!'}
        merchant_code = order and order.carrier_id and order.carrier_id.company_id and order.carrier_id.company_id.mondial_relay_merchant_code
        security_code = order and order.carrier_id and order.carrier_id.company_id and order.carrier_id.company_id.mondial_relay_security_code
        method_code = order and order.carrier_id and order.carrier_id.delivery_method_code
        try:
            data = "{0}{1}{2}{3}{4}{5}{6}".format(merchant_code, "FR",
                                                  recipient_address.city, recipient_address.zip,
                                                  method_code, "5",
                                                  security_code)
            result = hashlib.md5(data.encode())
            security_key = result.hexdigest().upper()
            point_ralais_request = etree.Element("Envelope")
            point_ralais_request.attrib['xmlns'] = "http://schemas.xmlsoap.org/soap/envelope/"
            body_node = etree.SubElement(point_ralais_request, "Body")
            point_relais_recherche = etree.SubElement(body_node, 'WSI4_PointRelais_Recherche')
            point_relais_recherche.attrib['xmlns'] = "http://www.mondialrelay.fr/webservice/"
            etree.SubElement(point_relais_recherche, 'Enseigne').text = str(merchant_code)
            etree.SubElement(point_relais_recherche, 'Pays').text = "FR"
            etree.SubElement(point_relais_recherche, 'Ville').text = str(recipient_address.city or "")
            etree.SubElement(point_relais_recherche, 'CP').text = str(recipient_address.zip or "")
            etree.SubElement(point_relais_recherche, 'Action').text = str(method_code)
            etree.SubElement(point_relais_recherche, 'NombreResultats').text = "5"
            etree.SubElement(point_relais_recherche, 'Security').text = str(security_key)

            headers = {
                'SOAPAction': 'http://www.mondialrelay.fr/webservice/WSI4_PointRelais_Recherche',
                'Content-Type': 'text/xml; charset="utf-8',
            }
            api_url = order.company_id.mondial_relay_api_url
            _logger.info(">>> sending post request to {}".format(api_url))
            _logger.info(">>> Request data {}".format(etree.tostring(point_ralais_request)))
            response_data = requests.post(url=api_url, headers=headers, data=etree.tostring(point_ralais_request))
            if response_data.status_code in [200, 201, 202]:
                _logger.info(">>> get successfully response from {}".format(api_url))
                response_data = Response(response_data)
                response_data = response_data.dict()
                location_list = response_data.get('Envelope') and response_data.get('Envelope').get(
                    'Body') and response_data.get('Envelope').get('Body').get(
                    'WSI4_PointRelais_RechercheResponse') and response_data.get('Envelope').get('Body').get(
                    'WSI4_PointRelais_RechercheResponse').get('WSI4_PointRelais_RechercheResult') and \
                                response_data.get('Envelope').get('Body').get('WSI4_PointRelais_RechercheResponse').get(
                                    'WSI4_PointRelais_RechercheResult').get('PointsRelais') and response_data.get(
                    'Envelope').get('Body').get('WSI4_PointRelais_RechercheResponse').get(
                    'WSI4_PointRelais_RechercheResult').get('PointsRelais').get('PointRelais_Details')
                mondial_relay_location_obj = request.env['mondialrelay.locations']
                request.env.cr.commit()
                existing_record = mondial_relay_location_obj.with_user(1).search([('sale_order_id', '=', order.id)])
                existing_record.with_user(1).unlink()
                if isinstance(location_list, list):
                    location_data = []
                    for location in location_list:
                        country = request.env['res.country'].sudo().search([('code', '=', location.get('Pays'))],
                                                                           limit=1)
                        name = location.get('LgAdr1')
                        name2 = location.get('LgAdr2')
                        street1 = location.get('LgAdr3')
                        street2 = location.get('LgAdr4')
                        zipcode = location.get('CP')
                        city = location.get('Ville')
                        mondial_relay_location_obj.sudo().create({
                            'point_relais_name': name,
                            'point_relais_name2': name2,
                            'point_relais_street': street1,
                            'point_relais_street2': street2,
                            'point_relais_zip': zipcode,
                            'point_relais_city': city,
                            'sale_order_id': order and order.id

                        })
                        location_data.append([name, street1, street2, zipcode, city])
                    values = {
                        'locations': order.mondial_relay_location_ids or []
                    }
                    template = request.env['ir.ui.view']._render_template('website_mondial_relay_integration'
                                                                          '.mondial_relay_location_details', values)
                    return {'template': template, 'dic': location_data}
                else:
                    return {'error': "{}".format(response_data)}

            else:
                return {'error': response_data.text}
        except Exception as e:
            return {'error': e}

    @http.route(['/set_location_mondial_relay'], type='json', auth='public', website=True, csrf=False)
    def set_location_mondial_relay(self, location=False, **post):
        location_id = request.env['mondialrelay.locations'].browse(location)
        if location_id and location_id.id:
            # location_id.sale_order_id.mondial_relay_location_id.unlink()
            location_id.sale_order_id.mondial_relay_location_id = location_id.id
            return {'success': True, 'name': location_id.point_relais_name, 'city': location_id.point_relais_city,
                    'zip': location_id.point_relais_zip, 'street': location_id.point_relais_street}
