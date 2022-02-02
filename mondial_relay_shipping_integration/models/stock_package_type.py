from odoo import fields, models, api


class StockPackageType(models.Model):
    _inherit = 'stock.package.type'
    package_carrier_type = fields.Selection(selection_add=[("mondial_relay_vts", "Mondial Relay")])