# -*- coding: utf-8 -*-
from odoo import models, fields, api


class DossierStudentLine(models.Model):
    _name = 'ersge.dossier.student.line'
    _description = 'Ligne élève du dossier'
    _rec_name = 'prenom'

    # Lien vers le dossier
    dossier_id = fields.Many2one(
        'ersge.dossier.famille',
        string='Dossier',
        required=True,
        ondelete='cascade'
    )

    # Lien vers l'élève — plus required
    student_id = fields.Many2one(
        'ersge.student',
        string='Élève',
        required=False
    )

    # Champs directs (plus de related)
    prenom = fields.Char(string='Prénom', readonly=False)
    nom = fields.Char(string='Nom', readonly=False)
    date_naissance = fields.Date(string='Date de naissance', readonly=False)
    sexe = fields.Selection([
        ('M', 'Masculin'),
        ('F', 'Féminin'),
    ], string='Sexe', readonly=False)
    classe = fields.Char(string='Classe')
    image_rights = fields.Boolean(
        string="Droit à l'image",
        readonly=False,
        default=True
    )

    # Forfait
    forfait_id = fields.Many2one('ersge.forfait', string='Forfait')
    forfait_montant_mensuel = fields.Float(
        related='forfait_id.montant_mensuel',
        string='Montant mensuel',
        store=True,
        readonly=True
    )

    # Création automatique de l'élève à la sauvegarde
    def _create_student_if_needed(self, dossier):
        for line in self:
            if not line.student_id and line.prenom and line.nom:
                student = self.env['ersge.student'].create({
                    'firstname': line.prenom,
                    'lastname': line.nom,
                    'name': f"{line.prenom} {line.nom}",
                    'birthdate': line.date_naissance,
                    'gender': line.sexe,
                    'image_rights': line.image_rights,
                    'family_id': dossier.family_id.id,
                })
                line.student_id = student