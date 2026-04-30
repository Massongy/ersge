# after_school_tarif.py
from odoo import models, fields


class AfterSchoolTarif(models.Model):
    _name = "ersge.after.school.tarif"
    _description = "Tarifs parascolaires"

    name = fields.Char(string="Nom", required=True)
    tarif_jardin_midi = fields.Float(string="Jardin - Midi (CHF)", default=150.0)
    tarif_jardin_soir = fields.Float(string="Jardin - Soir (CHF)", default=120.0)
    tarif_classe_midi = fields.Float(string="Classe - Midi (CHF)", default=180.0)
    tarif_classe_soir = fields.Float(string="Classe - Soir (CHF)", default=140.0)
    tarif_cirque = fields.Float(string="Accompagnement Cirque (CHF)", default=50.0)
    active = fields.Boolean(default=True)
    annee_scolaire = fields.Char(string="Année scolaire")
