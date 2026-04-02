# -*- coding: utf-8 -*-
from odoo import models, fields


class Extracurricular(models.Model):
    _name = 'ersge.extracurricular'
    _description = 'Activité parascolaire'
    _rec_name = 'name'

    name = fields.Char(string='Nom', required=True)
    montant_mensuel = fields.Float(string='Montant mensuel (CHF)', required=True)
    active = fields.Boolean(string='Actif', default=True)