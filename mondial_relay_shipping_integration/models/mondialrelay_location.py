from odoo import models, fields, api


class MondialRelayLocations(models.Model):
    _name = "mondialrelay.locations"
    _rec_name = "point_relais_name"
    point_relais_id = fields.Char(string="Point Relais Id", help="Point Relais Id Number")
    point_relais_name = fields.Char(string="Point Relais Name", help="Point Relais Name")
    point_relais_name2 = fields.Char(string="Point Relais name 2", help="point Relais Name2")
    point_relais_street = fields.Char(string="Point Relais Street", help="Point Relais street")
    point_relais_street2 = fields.Char(string="Point Relais Street 2", help="Point Relais street 2")
    point_relais_zip = fields.Char(string="Point Relais zip", help="Point Relais zip")
    point_relais_city = fields.Char(string="Point Relais City", help="Point Relay City")
    sale_order_id = fields.Many2one("sale.order", string="Sales Order")

    def set_location(self):
        self.sale_order_id.mondial_relay_location_id = self.id
