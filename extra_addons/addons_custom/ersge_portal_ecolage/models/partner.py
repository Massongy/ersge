# -*- coding: utf-8 -*-
from odoo import models, fields

class Partner(models.Model):
    _inherit = 'res.partner'

    is_parent = fields.Boolean(string='Est un parent', default=False)
    is_godfather = fields.Boolean(string='Est un parrain', default=False)
    is_employer = fields.Boolean(string='Est un employeur', default=False)
    family_id = fields.Many2one('ersge.family', string='Famille')
    employer_id = fields.Many2one(
        'res.partner', string='Employeur',
        domain="[('is_employer', '=', True)]"
    )