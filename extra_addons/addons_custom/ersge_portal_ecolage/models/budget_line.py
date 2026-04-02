# -*- coding: utf-8 -*-
from odoo import models, fields


class BudgetLine(models.Model):
    _name = 'ersge.budget.line'
    _description = 'Ligne budget mensuel'

    dossier_id = fields.Many2one('ersge.dossier.famille', string='Dossier', required=True, ondelete='cascade')
    category = fields.Char(string='Catégorie', required=True)
    description = fields.Char(string='Description')
    type = fields.Selection([
        ('income', 'Revenu'),
        ('expense', 'Charge'),
    ], string='Type', required=True)
    amount = fields.Float(string='Montant (CHF)', required=True)