# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AfterSchoolLine(models.Model):
    _name = "ersge.after.school.line"
    _description = "Inscription parascolaire détaillée"

    dossier_id = fields.Many2one(
        "ersge.dossier.famille", required=True, ondelete="cascade"
    )
    student_id = fields.Many2one("ersge.student", required=True)
    # Ajoutez ces deux champs après `student_id` ou à la fin de la classe
    student_firstname = fields.Char(
        related="student_id.firstname", string="Prénom", readonly=True
    )
    student_lastname = fields.Char(
        related="student_id.lastname", string="Nom", readonly=True
    )
    family_id = fields.Many2one(related="student_id.family_id", store=True)
    selected = fields.Boolean(string="Inscrire", default=False)
    accueil_type = fields.Selection(
        [
            ("jardin", "Jardin d'Accueil (3-6 ans)"),
            ("classe", "Classe d'Accueil (6-12 ans)"),
        ],
        required=False,
    )

    # Relation dynamique vers les prestations (définies en back-office)
    prestation_ids = fields.Many2many(
        "ersge.after.school.prestation", string="Prestations choisies"
    )

    montant_mensuel = fields.Monetary(compute="_compute_montant_mensuel", store=True)
    currency_id = fields.Many2one(
        "res.currency", default=lambda self: self.env.company.currency_id
    )
    display_name = fields.Char(compute="_compute_display_name", store=True)

    @api.depends("student_id", "accueil_type")
    def _compute_display_name(self):
        for rec in self:
            student_name = rec.student_id.display_name or "Élève"
            accueil_label = dict(rec._fields["accueil_type"].selection).get(
                rec.accueil_type, ""
            )
            rec.display_name = f"{student_name} - {accueil_label}"

    @api.depends("accueil_type", "prestation_ids")
    def _compute_montant_mensuel(self):
        for rec in self:
            total = 0.0
            if rec.accueil_type == "jardin":
                total = sum(rec.prestation_ids.mapped("prix_jardin"))
            else:
                total = sum(rec.prestation_ids.mapped("prix_classe"))
            rec.montant_mensuel = total
