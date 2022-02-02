import requests
import logging
from odoo import models, fields, api, _
from odoo.addons.mondial_relay_shipping_integration.models.mondial_relay_response import Response
from odoo.exceptions import Warning, ValidationError, UserError
import xml.etree.ElementTree as etree
import hashlib
import base64

_logger = logging.getLogger("Mondial Relay")


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(selection_add=[("mondial_relay_vts", "Mondial Relay")],
                                     ondelete={'mondial_relay_vts': 'set default'})
    package_id = fields.Many2one('stock.package.type', string="package", help="please select package type")
    delivery_method_code = fields.Selection([('24R', '24R - Point Relais® delivery'),
                                             ('24L', '24L - Point Relais® XL delivery'),
                                             ('DRI', 'DRI : Colis drive delivery'),
                                             ('LD1', 'LD1 : Home delivery  (1 delivery man)'),
                                             ('LCC', 'LCC : Home delivery  (2 delivery man)'),
                                             ('LDS', 'LDS : Home delivery (2 delivery men)'),
                                             ('ESP', 'ESP')
                                             ], help="Delivery Modes is Given By Mondial Relay")
    collection_mode = fields.Selection([('CCC', 'CCC'),
                                        ('CDR', 'CDR'),
                                        ('CDS', 'CDS'),
                                        ('REL', 'REL')], help="Collection Mode is Given By Mondial Relay")
    package_size = fields.Selection([('XS', 'XS'),
                                     ('S', 'S'),
                                     ('M', 'M'),
                                     ('L', 'L'),
                                     ('XL', 'XL'),
                                     ('XXL', 'XXL'),
                                     ('3XL', '3XL')], string="Size", help="Size Given By Mondial Relay")

    def mondial_relay_vts_rate_shipment(self, orders):
        "This Method Is Used For Get Rate"
        return {'success': True, 'price': 0.0, 'error_message': False, 'warning_message': False}

    @api.model
    def mondial_relay_vts_send_shipping(self, pickings):

        picking_partner_id = pickings.partner_id
        picking_company_id = pickings.picking_type_id.warehouse_id.partner_id
        if not picking_company_id.zip or not picking_company_id.city or not picking_company_id.country_id.code or not picking_company_id.phone or not picking_company_id.email:
            raise ValidationError("Please Define Proper Sender Address!")
        # check Receiver Address
        if not picking_partner_id.zip or not picking_partner_id.city or not picking_partner_id.country_id or not picking_partner_id.email or not picking_partner_id.phone:
            raise ValidationError("Please Define Proper Recipient Address!")
        grams = pickings.shipping_weight * 1000
        _logger.info(grams)

        """This Method Is Used For Send The Data To Shipper"""
        dest_lang = picking_partner_id.country_id and picking_partner_id.country_id.code
        point_relais_id = pickings.sale_id.mondial_relay_location_id.point_relais_id if pickings.sale_id and pickings.sale_id.mondial_relay_location_id and pickings.sale_id.mondial_relay_location_id.point_relais_id else "AUTO"
        live_relay = pickings.sale_id.mondial_relay_location_id.point_relais_id if pickings.sale_id and pickings.sale_id.mondial_relay_location_id and pickings.sale_id.mondial_relay_location_id.point_relais_id else ""
        collection_data = "{0}{1}{2}{3}{4}{5}{6}{7}{8}{9}{10}{11}{12}{13}{14}{15}{16}{17}{18}{19}{20}{21}{22}{23}{24}{25}{26}{27}{28}{29}{30}".format(
            self.company_id.mondial_relay_merchant_code or "", self.collection_mode or "",
            self.delivery_method_code or "", "FR", picking_company_id.name or "",
            picking_company_id.street or "", picking_company_id.city or "", picking_company_id.zip or "",
            "FR", picking_company_id.phone or "", picking_company_id.email, "FR",
            picking_partner_id.name or "", picking_partner_id.street or "", picking_partner_id.city or "",
            picking_partner_id.zip or "", dest_lang, picking_partner_id.phone or "",
            picking_partner_id.email or "", int(grams) or "", "1",
            int(pickings.sale_id.amount_total) or "", int(pickings.sale_id.amount_total) or "", "EUR", dest_lang,
            point_relais_id,
            dest_lang,
            live_relay, "N",
            "N", self.company_id.mondial_relay_security_code or "")
        result = hashlib.md5(collection_data.encode())
        security_key = result.hexdigest().upper()
        _logger.info(security_key)
        # _logger.info(collection_data)
        response = []
        for picking in pickings:
            total_bulk_weight = picking.weight_bulk
            picking_partner_id = picking.partner_id
            picking_company_id = picking.picking_type_id.warehouse_id.partner_id

            shipment_request = etree.Element("Envelope")
            shipment_request.attrib['xmlns'] = "http://schemas.xmlsoap.org/soap/envelope/"
            body_node = etree.SubElement(shipment_request, "Body")
            creation_label = etree.SubElement(body_node, 'WSI2_CreationEtiquette')
            creation_label.attrib['xmlns'] = "http://www.mondialrelay.fr/webservice/"
            etree.SubElement(creation_label, 'Enseigne').text = str(
                self.company_id and self.company_id.mondial_relay_merchant_code)
            etree.SubElement(creation_label, 'ModeCol').text = str(
                self.collection_mode)
            etree.SubElement(creation_label, 'ModeLiv').text = str(
                self.delivery_method_code)
            etree.SubElement(creation_label, 'NDossier').text = ""
            etree.SubElement(creation_label, 'NClient').text = ""
            etree.SubElement(creation_label, 'Expe_Langage').text = "FR"
            etree.SubElement(creation_label, 'Expe_Ad1').text = picking_company_id.name or ""
            etree.SubElement(creation_label, 'Expe_Ad2').text = ""
            etree.SubElement(creation_label, 'Expe_Ad3').text = picking_company_id.street or ""
            etree.SubElement(creation_label, 'Expe_Ad4').text = ""
            etree.SubElement(creation_label, 'Expe_Ville').text = picking_company_id.city or ""
            etree.SubElement(creation_label, 'Expe_CP').text = picking_company_id.zip or ""
            etree.SubElement(creation_label,
                             'Expe_Pays').text = picking_company_id.country_id and picking_company_id.country_id.code or ""
            etree.SubElement(creation_label, 'Expe_Tel1').text = picking_company_id.phone or ""
            etree.SubElement(creation_label, 'Expe_Tel2').text = ""
            etree.SubElement(creation_label, 'Expe_Mail').text = picking_company_id.email or ""

            etree.SubElement(creation_label, 'Dest_Langage').text = "FR"
            etree.SubElement(creation_label, 'Dest_Ad1').text = picking_partner_id.name or ""
            etree.SubElement(creation_label, 'Dest_Ad2').text = ""
            etree.SubElement(creation_label, 'Dest_Ad3').text = picking_partner_id.street or ""
            etree.SubElement(creation_label, 'Dest_Ad4').text = ""
            etree.SubElement(creation_label, 'Dest_Ville').text = picking_partner_id.city or ""
            etree.SubElement(creation_label, 'Dest_CP').text = picking_partner_id.zip or ""
            etree.SubElement(creation_label,
                             'Dest_Pays').text = picking_partner_id.country_id and picking_partner_id.country_id.code or ""
            etree.SubElement(creation_label, 'Dest_Tel1').text = picking_partner_id.phone or ""
            etree.SubElement(creation_label, 'Dest_Tel2').text = ""
            etree.SubElement(creation_label, 'Dest_Mail').text = picking_partner_id.email or ""
            etree.SubElement(creation_label, 'Poids').text = str(int(grams))
            etree.SubElement(creation_label, 'Longueur').text = ""
            etree.SubElement(creation_label, 'Taille').text = ""  # "%s" % (self.package_size)
            etree.SubElement(creation_label, 'NbColis').text = "1"
            etree.SubElement(creation_label, 'CRT_Valeur').text = str(
                int(picking.sale_id and picking.sale_id.amount_total))
            etree.SubElement(creation_label, 'CRT_Devise').text = ""
            etree.SubElement(creation_label, 'Exp_Valeur').text = str(
                int(picking.sale_id and picking.sale_id.amount_total))
            etree.SubElement(creation_label, 'Exp_Devise').text = "EUR"
            etree.SubElement(creation_label, 'COL_Rel_Pays').text = dest_lang
            etree.SubElement(creation_label,
                             'COL_Rel').text = point_relais_id  # picking.sale_id.mondial_relay_location_id.point_relais_id if picking.sale_id and picking.sale_id.mondial_relay_location_id and picking.sale_id.mondial_relay_location_id.point_relais_id else "AUTO"
            # etree.SubElement(creation_label,
            #                  'COL_Rel').text = picking.sale_id.mondial_relay_location_id.point_relais_id if picking.sale_id and picking.sale_id.mondial_relay_location_id and picking.sale_id.mondial_relay_location_id.point_relais_id else "AUTO"
            etree.SubElement(creation_label, 'LIV_Rel_Pays').text = dest_lang
            etree.SubElement(creation_label,
                             'LIV_Rel').text = live_relay  # picking.sale_id.mondial_relay_location_id.point_relais_id if picking.sale_id and picking.sale_id.mondial_relay_location_id and picking.sale_id.mondial_relay_location_id.point_relais_id else ""
            etree.SubElement(creation_label, 'TAvisage').text = "N"
            etree.SubElement(creation_label, 'TReprise').text = "N"
            etree.SubElement(creation_label, 'Montage').text = ""
            etree.SubElement(creation_label, 'TRDV').text = ""
            etree.SubElement(creation_label, 'Assurance').text = ""
            etree.SubElement(creation_label, 'Instructions').text = ""
            etree.SubElement(creation_label, 'Security').text = str(
                security_key)
            etree.SubElement(creation_label, 'Texte').text = ""

            try:
                headers = {
                    'SOAPAction': 'http://www.mondialrelay.fr/webservice/WSI2_CreationEtiquette',
                    'Content-Type': 'text/xml; charset="utf-8',
                }
                url = self.company_id and self.company_id.mondial_relay_api_url
                _logger.info(etree.tostring(shipment_request))
                response_data = requests.request(method="POST", url=url, headers=headers,
                                                 data=etree.tostring(shipment_request))
                _logger.info(response_data)
                api = Response(response_data)
                response_data = api.dict()
                _logger.info(response_data)
                status = response_data.get('Envelope').get('Body').get('WSI2_CreationEtiquetteResponse').get(
                    'WSI2_CreationEtiquetteResult')

                if status.get('ExpeditionNum'):
                    picking.mondial_relay_label_url = "http://www.mondialrelay.com" + status.get('URL_Etiquette')
                    pdf_url = picking.mondial_relay_label_url.replace("A4","10x15")
                    headers = {'Content-Type': "application/x-www-form-urlencoded", 'Accept': "application/pdf"}
                    pdf_response = requests.request("GET", url=pdf_url, headers=headers)
                    binary_data = base64.b64encode(pdf_response.content)
                    parcel_number = status.get('ExpeditionNum')
                    pickings.carrier_tracking_ref = parcel_number
                    logmessage = ("<b>Tracking Numbers:</b> %s") % (pickings.carrier_tracking_ref)
                    pickings.message_post(body=logmessage,
                                          attachments=[("%s.pdf" % (pickings.id), pdf_response.content)])
                    _logger.info(response_data)
                    shipping_data = {'exact_price': 0.0, 'tracking_number': parcel_number}
                    response += [shipping_data]
                    return response
                else:
                    raise ValidationError(
                        _("Shipment Number Not Found In Response \n Response Data {}").format(response_data))

            except Exception as e:
                raise ValidationError(e)

    def mondial_relay_vts_get_tracking_link(self, pickings):
        # collection_data_tracking = "{0}{1}{2}{3}".format(self.company_id.mondial_relay_merchant_code,
        #                                                  pickings.carrier_tracking_ref, "FR",
        #                                                  self.company_id.mondial_relay_security_code)
        # result_tracking = hashlib.md5(collection_data_tracking.encode())
        # result_tracking_upper = result_tracking.hexdigest().upper()
        # response = []
        # for picking in pickings:
        #     tracking_request = etree.Element("Envelope")
        #     tracking_request.attrib['xmlns'] = "http://schemas.xmlsoap.org/soap/envelope/"
        #     body = etree.SubElement(tracking_request, "Body")
        #     tracking_node = etree.SubElement(body, "WSI2_TracingColisDetaille")
        #     tracking_node.attrib['xmlns'] = "http://www.mondialrelay.fr/webservice/"
        #     etree.SubElement(tracking_node, 'Enseigne').text = self.company_id.mondial_relay_merchant_code
        #     etree.SubElement(tracking_node, 'Expedition').text = pickings.carrier_tracking_ref
        #     etree.SubElement(tracking_node, 'Langue').text = "FR"
        #     etree.SubElement(tracking_node, 'Security').text = result_tracking_upper
        #
        #     try:
        #         headers = {
        #             'SOAPAction': 'http://www.mondialrelay.fr/webservice/WSI2_TracingColisDetaille',
        #             'Content-Type': 'text/xml; charset="utf-8',
        #         }
        #         url = self.company_id and self.company_id.mondial_relay_api_url
        #         _logger.info(etree.tostring(tracking_request))
        #         response_data = requests.request(method="POST", url=url, headers=headers,
        #                                          data=etree.tostring(tracking_request))
        #         _logger.info(response_data)
        #         api = Response(response_data)
        #         response_data = api.dict()
        #         _logger.info(response_data)
        #         response_stat = response_data.get('Envelope').get('Body').get('WSI2_TracingColisDetailleResponse').get(
        #             'WSI2_TracingColisDetailleResult').get('STAT')
        #         parcel_information = response_data.get('Envelope') and response_data.get('Envelope').get('Body') and \
        #                         response_data.get('Envelope').get('Body').get('WSI2_TracingColisDetailleResponse') and \
        #                         response_data.get('Envelope').get('Body').get('WSI2_TracingColisDetailleResponse').get('WSI2_TracingColisDetailleResult') and\
        #                         response_data.get('Envelope').get('Body').get('WSI2_TracingColisDetailleResponse').get('WSI2_TracingColisDetailleResult').get('Libelle01')
        #         if not parcel_information:
        #             raise ValidationError("Response : %s"%response_data.get('Envelope').get('Body').get('WSI2_TracingColisDetailleResponse').get('WSI2_TracingColisDetailleResult').get('STAT'))
        #         if parcel_information:
        #             picking.tracking_details = response_stat + " - " + parcel_information
                res = "https://www.mondialrelay.fr/suivi-de-colis/"
                return res
            # except Exception as e:
            #     raise ValidationError(e)

    def mondial_relay_vts_cancel_shipment(self, picking):
        raise ValidationError("Cancel API is not available!")
