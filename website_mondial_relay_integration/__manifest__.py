# -*- coding: utf-8 -*-pack
{
    # App information
    'name': 'eCommerce Mondial Relay Integration',
    'category': 'Website',
    'version': '15.07.02.2022',
    'summary': """""",
    'description': """We are providing following modules, Shipping Operations, shipping, odoo shipping integration,odoo shipping connector, dhl express, fedex, ups, gls, usps, stamps.com, shipstation, bigcommerce, easyship, amazon shipping, sendclound, ebay, shopify.""",
    'depends': [
        'website_sale',
        'website_sale_delivery',
        'mondial_relay_shipping_integration',
    ],

    'data': [
        'views/template.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'website_mondial_relay_integration/static/src/css/mondial_relay.css',
            'website_mondial_relay_integration/static/src/js/mondial_relay.js'
        ],
    },
    'live_test_url': 'https://www.vrajatechnologies.com/contactus',
    'author': 'Vraja Technologies',
    'maintainer': 'Vraja Technologies',
    'website': 'www.vrajatechnologies.com',
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'price': '39',
    'currency': 'EUR',
    'license': 'OPL-1',

}
