# -*- coding: utf-8 -*-
from odoo import models, fields, api


class Partner(models.Model):
    _inherit = "res.partner"

    # Types de partenaires
    is_parent = fields.Boolean(string="Est un parent", default=False)
    is_godfather = fields.Boolean(string="Est un parrain", default=False)
    is_employer = fields.Boolean(string="Est un employeur", default=False)

    # Liens
    family_id = fields.Many2one("ersge.family", string="Famille")
    employer_id = fields.Many2one(
        "res.partner", string="Employeur", domain="[('is_employer', '=', True)]"
    )

    # Champs pour les parents (prénom, nom séparés)
    firstname = fields.Char(string="Prénom")
    lastname = fields.Char(string="Nom")

    # Téléphones multiples
    phone_mobile = fields.Char(string="Téléphone mobile")
    phone_fixed = fields.Char(string="Téléphone fixe")
    phone_pro = fields.Char(string="Téléphone professionnel")

    # Adresse complète (déjà existante dans res.partner mais on s'assure)
    # street, street2, zip, city, country_id existent déjà

    # Profession et employeur
    profession = fields.Char(string="Profession")
    employer_name = fields.Char(string="Nom de l'employeur")

    # Informations scolaires pour les élèves
    birthdate = fields.Date(string="Date de naissance")
    gender = fields.Selection(
        [
            ("M", "Masculin"),
            ("F", "Féminin"),
        ],
        string="Sexe",
    )
    image_rights = fields.Boolean(string="Droit à l'image", default=True)
    pronote_id = fields.Char(string="Identifiant ProNote")
    class_level = fields.Char(string="Classe")

    # Champs computed pour l'affichage
    def name_get(self):
        result = []
        for record in self:
            if record.firstname and record.lastname:
                name = f"{record.firstname} {record.lastname}"
            elif record.firstname:
                name = record.firstname
            elif record.lastname:
                name = record.lastname
            else:
                name = record.name or "Sans nom"
            result.append((record.id, name))
        return result
