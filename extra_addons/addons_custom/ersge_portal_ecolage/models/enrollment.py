# -*- coding: utf-8 -*-
from odoo import models, fields


class ErsgeEnrollment(models.Model):
    _name = 'ersge.enrollment'
    _description = 'Inscription scolaire'

    student_id = fields.Many2one(
        'ersge.student',
        string='Élève',
        required=True,
        ondelete='restrict'
    )
    annee_scolaire = fields.Char(
        string='Année scolaire',
        required=True
    )

    # === FORFAIT ===
    forfait_id = fields.Many2one(
        'product.template',
        string='Forfait',
        domain=[('is_forfait', '=', True)]
    )
    monthly_amount = fields.Float(
        string='Montant mensuel écolage',
        related='forfait_id.list_price',
        store=True
    )

    # === PARASCOLAIRE ===
    after_school = fields.Boolean(
        string='Inscrit au parascolaire',
        default=False
    )
    after_school_type = fields.Selection([
        ('jardin', 'Jardin d\'Accueil (3-6 ans)'),
        ('classe', 'Classe d\'Accueil (6-12 ans)'),
    ], string='Type parascolaire')

    after_school_amount = fields.Float(
        string='Montant mensuel parascolaire',
        default=0.0
    )

    # === CRÉNEAUX PARASCOLAIRE ===
    slot_ids = fields.One2many(
        'ersge.slot',
        'enrollment_id',
        string='Créneaux'
    )

    # === STATUT ===
    state = fields.Selection([
        ('draft',     'Brouillon'),
        ('confirmed', 'Confirmé'),
        ('cancelled', 'Annulé'),
    ], string='Statut', default='draft')


class ErsgeSlot(models.Model):
    _name = 'ersge.slot'
    _description = 'Créneau parascolaire'

    enrollment_id = fields.Many2one(
        'ersge.enrollment',
        string='Inscription',
        required=True,
        ondelete='cascade'
    )
    day = fields.Selection([
        ('monday',   'Lundi'),
        ('tuesday',  'Mardi'),
        ('thursday', 'Jeudi'),
        ('friday',   'Vendredi'),
    ], string='Jour', required=True)

    time_slot = fields.Selection([
        ('12_15',  '12h00 - 15h30'),
        ('15_17',  '15h30 - 17h45'),
        ('cirque', 'Accompagnement Cirque'),
    ], string='Créneau', required=True)

    waitlist = fields.Boolean(string='Liste d\'attente', default=False)
    price = fields.Float(string='Prix mensuel', default=0.0)