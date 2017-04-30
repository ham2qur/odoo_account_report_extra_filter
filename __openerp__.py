{
    "name": "ACC:Report Filter",
    "version": "1.0",
    'author': 'Falinwa',
    "description": """
    Module to add additional filter feature on account report
    """,
    "depends" : ['base', 'account', 'account_reports', 'fal_parent_account', 'fal_business_unit'],
    'init_xml': [],
    'update_xml': [
        'views/account_view.xml',
    ],
    'css': [],
    'js' : [],
    'qweb': [
        'static/src/xml/account_report_backend.xml',
    ],
    'installable': True,
    'active': False,
    'application' : False,
}