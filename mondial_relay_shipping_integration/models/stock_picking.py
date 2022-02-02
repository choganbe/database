from odoo import models, fields, api, _


class MondialRelayShipmentNumber(models.Model):
    _inherit = 'stock.picking'

    mondial_relay_label_url = fields.Char(string="Mondial Relay Label Url", copy=False, readonly=True,
                                          help="Url for Generate Label")
    # tracking_details = fields.Char(string="Tracking Details", copy=False, readonly=True)
