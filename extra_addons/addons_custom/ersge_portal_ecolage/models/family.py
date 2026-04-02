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