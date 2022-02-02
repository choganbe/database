from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    use_mondial_relay_shipping_provider = fields.Boolean(string="Is Use Mondial Relay Shipping Provider",
                                                         help="True when we need to use Mondial Relay shipping provider",
                                                         default=False, copy=False)
    mondial_relay_api_url = fields.Char(string='Mondial Relay API URL',
                                        default="https://api.mondialrelay.com/Web_Services.asmx",
                                        help="Get URL details from Mondial Relay")
    mondial_relay_merchant_code = fields.Char(string='Mondial Relay Merchant Number',
                                         help="This parameter is the merchant id code given in the document of parameters.")
    mondial_relay_security_code = fields.Char(string='Mondial Relay Security Code',
                                              help="Get Mondial Relay Security Code from process of md5 Algorithm")
