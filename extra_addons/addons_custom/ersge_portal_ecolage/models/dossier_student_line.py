# -*- coding: utf-8 -*-
from odoo import models, fields


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

    # Lien vers l'élève
    student_id = fields.Many2one(
        'ersge.student',
        string='Élève', 
        required=True
    )

    # Champs liés à l'élève pour affichage dans la vue
    prenom = fields.Char(
        related='student_id.firstname', 
        string='Prénom', 
        store=True
    )
    nom = fields.Char(
        related='student_id.lastname', 
        string='Nom', 
        store=True
    )
    date_naissance = fields.Date(
        related='student_id.birthdate', 
        string='Date de naissance', 
        store=True
    )
    sexe = fields.Selection(
        related='student_id.gender', 
        string='Sexe', 
        store=True
    )
    classe = fields.Char(string='Classe')
    image_rights = fields.Boolean(
        related='student_id.image_rights', 
        string='Droit à l\'image', 
        store=True
    )

    # Forfait lié à l'élève
    forfait_id = fields.Many2one(
        'ersge.forfait', 
        string='Forfait'
    )
    forfait_montant_mensuel = fields.Float(
        related='forfait_id.montant_mensuel', 
        string='Montant mensuel', 
        store=True
    )