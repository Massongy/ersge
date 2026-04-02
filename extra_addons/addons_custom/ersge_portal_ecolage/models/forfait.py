# -*- coding: utf-8 -*-
from odoo import models, fields


class Forfait(models.Model):
    _name = 'ersge.forfait'
    _description = 'Forfait scolaire'
    _rec_name = 'name'

    name = fields.Char(string='Nom', required=True)
    montant_mensuel = fields.Float(string='Montant mensuel (CHF)', required=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Actif', default=True)