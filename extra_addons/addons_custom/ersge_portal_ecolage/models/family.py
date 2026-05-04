# -*- coding: utf-8 -*-
from odoo import models, fields

class ErsgeFamily(models.Model):
    _name = 'ersge.family'
    _description = 'Famille'

    name = fields.Char(string='Nom de la famille', required=True)
    parent_ids = fields.One2many('res.partner', 'family_id', string='Parents')
    is_teacher = fields.Boolean(string="Famille enseignante", default=False)
    student_ids = fields.One2many('ersge.student', 'family_id', string='Élèves')
    dossier_ids = fields.One2many('ersge.dossier.famille', 'family_id', string='Dossiers')
    godfather_ids = fields.Many2many(
        'res.partner',
        'ersge_family_godfather_rel',
        'family_id',
        'partner_id',
        string='Parrains'
    )
    active = fields.Boolean(default=True)
    email = fields.Char(string="Email principal", compute='_compute_email', store=False)

    # ----- NOUVEAUX CHAMPS POUR LES INVITATIONS -----
    invitation_token = fields.Char(string="Token d'invitation", copy=False, index=True)
    invitation_expiration = fields.Datetime(string="Date d'expiration du token")
    invited_partner_ids = fields.Many2many(
        'res.partner',
        'family_invitation_rel',
        'family_id',
        'partner_id',
        string="Membres invités (en attente)"
    )
    # (optionnel) – pour stocker le rôle proposé dans l'invitation
    invited_role = fields.Selection([
        ('parent2', 'Parent 2'),
        ('tutor', 'Tuteur')
    ], string="Rôle proposé dans l'invitation en cours")

    def _compute_email(self):
        for family in self:
            family.email = family.parent_ids[:1].email if family.parent_ids else False

    # Méthode pour générer un token (dans le contrôleur)