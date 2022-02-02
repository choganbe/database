# -*- coding: utf-8 -*-pack
{
    # App information
    'name': 'Mondial Relay Shipping Integration',
    'category': 'Website',
    'version': '15.0.27.10.21',
    'summary': """Using Mondial Relay Easily manage Shipping Operation in odoo.Export Order While Validate Delivery Order.Import Tracking From Mondial Relay to odoo.Generate Label in odoo.We also Provide the gls,mrw,colissimo,dbschenker shipping integration.""",
    'description': """""",
    'depends': ['delivery'],
    'live_test_url': 'http://www.vrajatechnologies.com/contactus',
    'data': ['view/res_company.xml',
             'view/delivery_carrier_view.xml',
             'view/stock_picking.xml',
             'view/sale_view.xml',
             'security/ir.model.access.csv'],
    'images': ['static/description/mondialrelay_odoo_Shipping_Integration.jpg'],
    'author': 'Vraja Technologies',
    'maintainer': 'Vraja Technologies',
    'website': 'www.vrajatechnologies.com',
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'price': "279",
    'currency': 'EUR',
    'license': 'OPL-1',
}
#15.0.27.10.21 initial stage

