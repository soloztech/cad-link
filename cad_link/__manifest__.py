# SPDX-License-Identifier: LGPL-3.0-or-later
{
    "name": "CAD-link",
    "summary": "Read shared CAD documents from Odoo products",
    "version": "16.0.1.0.0",
    "development_status": "Alpha",
    "category": "Manufacturing",
    "author": "CAD-link contributors",
    "website": "https://github.com/soloztech/cad-link",
    "license": "LGPL-3",
    "depends": ["product", "web", "fs_storage"],
    "data": [
        "security/cad_security.xml",
        "views/company_views.xml",
        "views/product_views.xml",
        "views/document_templates.xml",
    ],
    "installable": True,
    "application": False,
}
