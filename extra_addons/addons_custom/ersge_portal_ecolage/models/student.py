# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ErsgeStudent(models.Model):
    _name = "ersge.student"
    _description = "Élève"
    _rec_name = "display_name"

    display_name = fields.Char(
        compute="_compute_display_name",
        store=True,
    )

    firstname = fields.Char(string="Prénom", required=False)
    lastname = fields.Char(string="Nom", required=False)
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

    family_id = fields.Many2one(
        "ersge.family", string="Famille", required=True, ondelete="restrict"
    )
    active = fields.Boolean(default=True)

    def name_get(self):
        result = []
        for student in self:
            name = f"{student.firstname} {student.lastname}".strip()
            if not name:
                name = "Nouvel élève"
            result.append((student.id, name))
        return result

    @api.model
    def create(self, vals_list):
        if isinstance(vals_list, dict):
            vals_list = [vals_list]

        for vals in vals_list:
            # Récupérer family_id depuis vals ou depuis le contexte
            family_id = vals.get("family_id")
            if not family_id and self.env.context.get("default_family_id"):
                family_id = self.env.context.get("default_family_id")

            if not vals.get("lastname") and family_id:
                family = self.env["ersge.family"].browse(family_id)
                vals["lastname"] = family.name

            # Si firstname est vide mais pas lastname, on peut mettre un placeholder
            if not vals.get("firstname") and vals.get("lastname"):
                vals["firstname"] = "Nouvel élève"

        return super().create(vals_list)

    @api.depends("firstname", "lastname")
    def _compute_display_name(self):
        for student in self:
            name = f"{student.firstname or ''} {student.lastname or ''}".strip()
            student.display_name = name or "Nouvel élève"
