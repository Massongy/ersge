# -*- coding: utf-8 -*-
from odoo import models, fields

class ErsgeFamily(models.Model):
    _name = 'ersge.family'
    _description = 'Famille'

    name = fields.Char(string='Nom de la famille', required=True)
    parent_ids = fields.One2many(
        'res.partner', 'family_id',
        string='Parents'
    )

    is_teacher = fields.Boolean(string="Famille enseignante", default=False)
    
    student_ids = fields.One2many(
        'ersge.student', 'family_id',
        string='Élèves'
    )
    
    dossier_ids = fields.One2many(
        'ersge.dossier.famille', 'family_id',
        string='Dossiers'
    )
    godfather_ids = fields.Many2many(
        'res.partner',
        'ersge_family_godfather_rel',  # table pivot explicite ← OBLIGATOIRE
        'family_id',
        'partner_id',
        string='Parrains'
    )
    active = fields.Boolean(default=True)

    email = fields.Char(string="Email principal", compute='_compute_email', store=False)

    def _compute_email(self):
        for family in self:
            # Prend l'email du premier parent
            if family.parent_ids:
                family.email = family.parent_ids[0].email
            else:
                family.email = False