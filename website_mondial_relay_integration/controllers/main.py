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
        try:
            order.get_locations()
            values = {
                'locations': order.mondial_relay_location_ids or []
            }
            template = request.env['ir.ui.view']._render_template('website_mondial_relay_integration'
                                                                  '.mondial_relay_location_details', values)

            return {'template': template}
        except Exception as e:
            return {'error': "Location not found. Please enter proper shipping details or contact us for support.\n\n{}".format(e)}

    @http.route(['/set_location_mondial_relay'], type='json', auth='public', website=True, csrf=False)
    def set_location_mondial_relay(self, location=False, **post):
        location_id = request.env['mondialrelay.locations'].browse(location)
        if location_id and location_id.id:
            # location_id.sale_order_id.mondial_relay_location_id.unlink()
            location_id.sale_order_id.mondial_relay_location_id = location_id.id
            return {'success': True, 'name': location_id.point_relais_name, 'city': location_id.point_relais_city,
                    'zip': location_id.point_relais_zip, 'street': location_id.point_relais_street}
