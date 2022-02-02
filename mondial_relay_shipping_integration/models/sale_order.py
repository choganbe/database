from odoo.exceptions import ValidationError
from odoo import models, fields, api, _
from requests import request
import base64
import hashlib
import xml.etree.ElementTree as etree
from odoo.addons.mondial_relay_shipping_integration.models.mondial_relay_response import Response


class SaleOrder(models.Model):
    _inherit = "sale.order"

    mondial_relay_location_ids = fields.One2many("mondialrelay.locations", "sale_order_id",
                                                 string="Mondial Relay Locations")
    mondial_relay_location_id = fields.Many2one("mondialrelay.locations", string="Mondial Relay Locations",
                                                help="Mondial Relay locations", copy=False)

    def get_locations(self):
        order = self
        # Shipper and Recipient Address
        shipper_address = order.warehouse_id.partner_id
        recipient_address = order.partner_shipping_id
        # check sender Address
        if not shipper_address.zip or not shipper_address.city or not shipper_address.country_id:
            raise ValidationError("Please Define Proper Sender Address!")
        # check Receiver Address
        if not recipient_address.zip or not recipient_address.city or not recipient_address.country_id:
            raise ValidationError("Please Define Proper Recipient Address!")
        if not self.carrier_id.company_id:
            raise ValidationError("Credential not available!")

        try:
            data = "{0}{1}{2}{3}{4}{5}{6}".format(self.company_id.mondial_relay_merchant_code, "FR",
                                                  recipient_address.city, recipient_address.zip,
                                                  self.carrier_id.delivery_method_code, "5",
                                                  self.company_id.mondial_relay_security_code)
            result = hashlib.md5(data.encode())
            security_key = result.hexdigest().upper()

            point_ralais_request = etree.Element("Envelope")
            point_ralais_request.attrib['xmlns'] = "http://schemas.xmlsoap.org/soap/envelope/"
            body_node = etree.SubElement(point_ralais_request, "Body")
            point_relais_recherche = etree.SubElement(body_node, 'WSI4_PointRelais_Recherche')
            point_relais_recherche.attrib['xmlns'] = "http://www.mondialrelay.fr/webservice/"
            etree.SubElement(point_relais_recherche, 'Enseigne').text = str(
                self.company_id and self.company_id.mondial_relay_merchant_code)
            etree.SubElement(point_relais_recherche, 'Pays').text = "FR"
            etree.SubElement(point_relais_recherche, 'Ville').text = str(recipient_address.city or "")
            etree.SubElement(point_relais_recherche, 'CP').text = str(recipient_address.zip or "")
            etree.SubElement(point_relais_recherche, 'Action').text = str(self.carrier_id.delivery_method_code)
            etree.SubElement(point_relais_recherche, 'NombreResultats').text = "5"
            etree.SubElement(point_relais_recherche, 'Security').text = str(security_key)
        except Exception as e:
            raise ValidationError(e)

        try:
            headers = {
                'SOAPAction': 'http://www.mondialrelay.fr/webservice/WSI4_PointRelais_Recherche',
                'Content-Type': 'text/xml; charset="utf-8',
            }
            URL = self.company_id.mondial_relay_api_url
            response_data = request(method='POST', url=URL, headers=headers, data=etree.tostring(point_ralais_request))
        except Exception as e:
            raise ValidationError(e)
        if response_data.status_code in [200, 201]:
            api = Response(response_data)
            response_data = api.dict()
            mondial_relay_locations = self.env['mondialrelay.locations']
            existing_records = self.env['mondialrelay.locations'].search(
                [('sale_order_id', '=', order and order.id)])
            existing_records.sudo().unlink()

            if response_data:
                if isinstance(response_data, dict):
                    response_data = [response_data]
                locations = response_data[0] and response_data[0].get('Envelope').get('Body') and \
                            response_data[0].get('Envelope').get('Body').get('WSI4_PointRelais_RechercheResponse') and \
                            response_data[0].get('Envelope').get('Body').get('WSI4_PointRelais_RechercheResponse').get('WSI4_PointRelais_RechercheResult').get('PointsRelais') and \
                            response_data[0].get('Envelope').get('Body').get('WSI4_PointRelais_RechercheResponse').get('WSI4_PointRelais_RechercheResult').get('PointsRelais').get('PointRelais_Details')
                if locations == None:
                    raise ValidationError("%s" % (response_data))
                for location in locations:
                    point_relais_id = location.get('Num')
                    point_relais_name = location.get('LgAdr1')
                    point_relais_name2 = location.get('LgAdr2')
                    point_relais_street = location.get('LgAdr3')
                    point_relais_street2 = location.get('LgAdr4')
                    point_relais_zip = location.get('CP')
                    point_relais_city = location.get('Ville')

                    sale_order_id = self.id
                    point_relais_id = mondial_relay_locations.sudo().create(
                        {'point_relais_name': "%s" % (point_relais_name),
                         'point_relais_name2': "%s" % (point_relais_name2),
                         'point_relais_id': point_relais_id,
                         'point_relais_street': point_relais_street,
                         'point_relais_street2': point_relais_street2,
                         'point_relais_zip': point_relais_zip,
                         'point_relais_city': point_relais_city,
                         'sale_order_id': sale_order_id})
            else:
                raise ValidationError("Location Not Found For This Address! %s " % (response_data))
        else:
            raise ValidationError("%s %s" % (response_data, response_data.text))
