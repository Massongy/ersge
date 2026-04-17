# -*- coding: utf-8 -*-
from odoo import models, fields, api


class DossierStudentLine(models.Model):
    _name = 'ersge.dossier.student.line'
    _description = 'Ligne élève du dossier'
    _rec_name = 'student_id'

    dossier_id = fields.Many2one('ersge.dossier.famille', required=True, ondelete='cascade')
    student_id = fields.Many2one('ersge.student', string='Élève', required=True)

    # Ces champs sont des "fenêtres" sur student_id (une seule source de vérité)
    prenom = fields.Char(string='Prénom', related='student_id.firstname', store=True, readonly=False)
    nom = fields.Char(string='Nom', related='student_id.lastname', store=True, readonly=False)
    date_naissance = fields.Date(string='Date de naissance', related='student_id.birthdate', store=True, readonly=False)
    sexe = fields.Selection([('M', 'Masculin'), ('F', 'Féminin')], string='Sexe', related='student_id.gender', store=True, readonly=False)
    image_rights = fields.Boolean(string="Droit à l'image", related='student_id.image_rights', store=True, readonly=False)
    
    classe = fields.Char(string='Classe')
    forfait_id = fields.Many2one('ersge.forfait', string='Forfait')
    forfait_montant_mensuel = fields.Float(related='forfait_id.montant_mensuel', store=True, readonly=True)

    @api.model
    def create(self, vals_list):
        # Si c'est un dict, transforme en liste
        if isinstance(vals_list, dict):
            vals_list = [vals_list]
        
        for vals in vals_list:
            # DEBUG - Ajoute ces 2 lignes
            print("DEBUG vals:", vals)
            
            if not vals.get('student_id') and vals.get('prenom') and vals.get('nom'):
                # DEBUG - Ajoute cette ligne
                print("DEBUG: Création d'un étudiant pour", vals.get('prenom'), vals.get('nom'))
                
                student = self.env['ersge.student'].create({
                    'firstname': vals['prenom'],
                    'lastname': vals['nom'],
                    'birthdate': vals.get('date_naissance'),
                    'gender': vals.get('sexe'),
                    'image_rights': vals.get('image_rights', True),
                    'family_id': self.env.context.get('default_dossier_id') or vals.get('dossier_id'),
                })
                vals['student_id'] = student.id
        
        return super().create(vals_list)