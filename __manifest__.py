{
    'name': 'FBR Integration Module',
    'version': '1.0',
    'summary': 'Integrate Odoo invoices with FBR demo account, store confirmed invoices, generate QR codes, and sync with FBR API.',
    'author': 'Usama Asif',
    'category': 'Accounting',
    'depends': ['base', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'views/fbr_integration_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
} 