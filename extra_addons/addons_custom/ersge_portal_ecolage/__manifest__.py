{
    'name': 'ERSGE - Portail Écolage',
    'version': '19.0.1.0.0',
    'summary': 'Portail écolage pour les familles',
    'author': 'ERSGE',
    'website': '',
    'category': 'Education',
    'depends': [
        'base',
        'portal',
        'website',
        'mail',
        'contacts',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/family_views.xml',
        'views/after_school_line_views.xml',
        'views/dossier_famille_views.xml',
        'views/partners.xml',
    ],
    'demo': [
        'demo/demo_data.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}