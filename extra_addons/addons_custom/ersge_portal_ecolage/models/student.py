# -*- coding: utf-8 -*-
from odoo import models, fields

class ErsgeStudent(models.Model):
    _name = 'ersge.student'
    _description = 'Élève'

    name = fields.Char(string='Nom complet', required=True)
    firstname = fields.Char(string='Prénom', required=True)
    lastname = fields.Char(string='Nom', required=True)
    birthdate = fields.Date(string='Date de naissance')
    gender = fields.Selection([
        ('M', 'Masculin'),
        ('F', 'Féminin'),
    ], string='Sexe')
    image_rights = fields.Boolean(string='Droit à l\'image', default=True)
    pronote_id = fields.Char(string='Identifiant ProNote')

    family_id = fields.Many2one(
        'ersge.family',
        string='Famille',
        required=True,
        ondelete='restrict'
    )
    active = fields.Boolean(default=True)