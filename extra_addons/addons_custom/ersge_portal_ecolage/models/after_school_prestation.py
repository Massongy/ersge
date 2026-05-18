# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AfterSchoolPrestation(models.Model):
    _name = "ersge.after.school.prestation"
    _description = "Prestation parascolaire (jour, créneau, prix)"
    _order = "jour, creneau"

    name = fields.Char(string="Libellé", required=True, translate=True)
    jour = fields.Selection(
        [
            ("lundi", "Lundi"),
            ("mardi", "Mardi"),
            ("mercredi", "Mercredi"),
            ("jeudi", "Jeudi"),
            ("vendredi", "Vendredi"),
        ],
        required=True,
    )
    creneau = fields.Selection(
        [
            ("midi", "Midi (12h-15h30)"),
            ("soir", "Soir (15h30-17h45)"),
            ("cirque", "Accompagnement Cirque"),
        ],
        required=True,
    )
    prix_jardin = fields.Monetary(
        string="Prix Jardin (3-6 ans)", required=True, currency_field="currency_id"
    )
    prix_classe = fields.Monetary(
        string="Prix Classe (6-12 ans)", required=True, currency_field="currency_id"
    )
    active = fields.Boolean(default=True)
    currency_id = fields.Many2one(
        "res.currency", default=lambda self: self.env.company.currency_id
    )

    applicable_to = fields.Selection(
    [
        ("jardins_enfants", "Jardins d'Enfants (2-3 ans)"),
        ("jardin", "Jardin d'Accueil (3-6 ans)"),
        ("classe", "Classe d'Accueil (6-12 ans)"),
    ],
    string="Applicable à",
    required=True,
    default="jardin",
)
