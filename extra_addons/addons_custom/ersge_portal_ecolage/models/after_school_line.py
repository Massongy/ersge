# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AfterSchoolLine(models.Model):
    _name = 'ersge.after.school.line'
    _description = 'Inscription parascolaire détaillée'
    _rec_name = 'display_name'

    dossier_id = fields.Many2one('ersge.dossier.famille', string='Dossier', required=True, ondelete='cascade')
    student_id = fields.Many2one('ersge.student', string='Élève', required=True)
    selected = fields.Boolean(string="Inscrire", default=True)  # Case à cocher

    # Type d'accueil
    accueil_type = fields.Selection([
        ('jardin', "Jardin d'Accueil (3-6 ans)"),
        ('classe', "Classe d'Accueil (6-12 ans)"),
    ], string="Type d'accueil")

    # Horaires par jour
    lundi_midi = fields.Boolean(string="Lundi 12h-15h30")
    lundi_soir = fields.Boolean(string="Lundi 15h30-17h45")
    lundi_cirque = fields.Boolean(string="Lundi Accompagnement Cirque")
    mardi_midi = fields.Boolean(string="Mardi 12h-15h30")
    mardi_soir = fields.Boolean(string="Mardi 15h30-17h45")
    mardi_cirque = fields.Boolean(string="Mardi Accompagnement Cirque")
    mercredi_midi = fields.Boolean(string="Mercredi 12h-15h30")
    mercredi_soir = fields.Boolean(string="Mercredi 15h30-17h45")
    mercredi_cirque = fields.Boolean(string="Mercredi Accompagnement Cirque")
    jeudi_midi = fields.Boolean(string="Jeudi 12h-15h30")
    jeudi_soir = fields.Boolean(string="Jeudi 15h-30h45")
    jeudi_cirque = fields.Boolean(string="Jeudi Accompagnement Cirque")
    vendredi_midi = fields.Boolean(string="Vendredi 12h-15h30")
    vendredi_soir = fields.Boolean(string="Vendredi 15h30-17h45")
    vendredi_cirque = fields.Boolean(string="Vendredi Accompagnement Cirque")

    # Montant mensuel calculé
    montant_mensuel = fields.Float(
        string="Montant mensuel (CHF)",
        compute='_compute_montant_mensuel',
        store=True
    )

    # Affichage
    display_name = fields.Char(compute='_compute_display_name', store=True)

    @api.depends('student_id', 'accueil_type')
    def _compute_display_name(self):
        for rec in self:
            student_name = rec.student_id.display_name or "Élève"
            accueil_label = dict(rec._fields['accueil_type'].selection).get(rec.accueil_type, '')
            rec.display_name = f"{student_name} - {accueil_label}"

    @api.depends(
        'accueil_type',
        'lundi_midi', 'lundi_soir', 'lundi_cirque',
        'mardi_midi', 'mardi_soir', 'mardi_cirque',
        'mercredi_midi', 'mercredi_soir', 'mercredi_cirque',
        'jeudi_midi', 'jeudi_soir', 'jeudi_cirque',
        'vendredi_midi', 'vendredi_soir', 'vendredi_cirque'
    )
    def _compute_montant_mensuel(self):
        TARIF_JARDIN_MIDI = 150.0
        TARIF_JARDIN_SOIR = 120.0
        TARIF_CLASSE_MIDI = 180.0
        TARIF_CLASSE_SOIR = 140.0
        TARIF_CIRQUE = 50.0

        for rec in self:
            total = 0.0
            if rec.accueil_type == 'jardin':
                if rec.lundi_midi: total += TARIF_JARDIN_MIDI
                if rec.lundi_soir: total += TARIF_JARDIN_SOIR
                if rec.mardi_midi: total += TARIF_JARDIN_MIDI
                if rec.mardi_soir: total += TARIF_JARDIN_SOIR
                if rec.mercredi_midi: total += TARIF_JARDIN_MIDI
                if rec.mercredi_soir: total += TARIF_JARDIN_SOIR
                if rec.jeudi_midi: total += TARIF_JARDIN_MIDI
                if rec.jeudi_soir: total += TARIF_JARDIN_SOIR
                if rec.vendredi_midi: total += TARIF_JARDIN_MIDI
                if rec.vendredi_soir: total += TARIF_JARDIN_SOIR
            else:  # classe
                if rec.lundi_midi: total += TARIF_CLASSE_MIDI
                if rec.lundi_soir: total += TARIF_CLASSE_SOIR
                if rec.lundi_cirque: total += TARIF_CIRQUE
                if rec.mardi_midi: total += TARIF_CLASSE_MIDI
                if rec.mardi_soir: total += TARIF_CLASSE_SOIR
                if rec.mardi_cirque: total += TARIF_CIRQUE
                if rec.mercredi_midi: total += TARIF_CLASSE_MIDI
                if rec.mercredi_soir: total += TARIF_CLASSE_SOIR
                if rec.mercredi_cirque: total += TARIF_CIRQUE
                if rec.jeudi_midi: total += TARIF_CLASSE_MIDI
                if rec.jeudi_soir: total += TARIF_CLASSE_SOIR
                if rec.jeudi_cirque: total += TARIF_CIRQUE
                if rec.vendredi_midi: total += TARIF_CLASSE_MIDI
                if rec.vendredi_soir: total += TARIF_CLASSE_SOIR
                if rec.vendredi_cirque: total += TARIF_CIRQUE

            rec.montant_mensuel = total