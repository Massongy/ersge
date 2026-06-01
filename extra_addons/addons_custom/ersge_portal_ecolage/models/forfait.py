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
    class_number = fields.Integer(
        string='Numéro de classe',
        help="Numéro de la classe (ex: 1 pour 1ère, 12 pour 12e, 0 pour jardins d'enfants, -1 pour autres)"
    )