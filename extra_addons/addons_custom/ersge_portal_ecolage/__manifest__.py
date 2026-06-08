{
    "name": "ERSGE - Portail Écolage",
    "version": "19.0.1.0.0",
    "summary": "Portail écolage pour les familles",
    "author": "ERSGE",
    "website": "",
    "category": "Education",
    "depends": [
        "base",
        "portal",
        "website",
        "mail",
        "contacts",
        "account",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/budget_categories.xml",
        "data/sequence_data.xml",
        "data/after_school_prestation.xml",
        'views/portal_acces_templates.xml',
        "views/forfait_views.xml",
        "views/after_school_prestation_views.xml",
        "views/family_views.xml",
        "views/dossier_famille_views.xml",
        "views/partners_views.xml",
        "views/student_views.xml",
        "views/portal_views.xml",
        "views/portal_my_dossiers_views.xml",
        "views/portal_dossier_famille_form_portal_views.xml",
        'views/portal_my_families.xml',
    ],
    "demo": [
        "demo/demo_data.xml",
    ],
    "installable": True,
    "application": True,
    "license": "LGPL-3",
    "assets": {
        "web.assets_frontend": [
            "ersge_portal_ecolage/static/src/js/portal_dossier.js",
            'https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/js/bootstrap.bundle.min.js',
        ],
    }
    
}
