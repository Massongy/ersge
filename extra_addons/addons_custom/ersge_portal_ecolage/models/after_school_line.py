# -*- coding: utf-8 -*-
from odoo import models, fields


class AfterSchoolLine(models.Model):
    _name = 'ersge.after.school.line'
    _description = 'Ligne activité parascolaire'

    dossier_id = fields.Many2one('ersge.dossier.famille', string='Dossier', required=True, ondelete='cascade')
    extracurricular_id = fields.Many2one('ersge.extracurricular', string='Activité')
    student_id = fields.Many2one('ersge.student', string='Élève')
    schedule = fields.Char(string='Emploi du temps')
    montant_mensuel = fields.Float(related='extracurricular_id.montant_mensuel', string='Montant mensuel', store=True)