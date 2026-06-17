# -*- coding: utf-8 -*-
from odoo import models, fields, _
from odoo.exceptions import UserError


class ErsgeFamily(models.Model):
    _name = 'ersge.family'
    _description = 'Famille'

    name = fields.Char(string='Nom de la famille', required=True)
    partner_ids = fields.Many2many(
        'res.partner',
        'ersge_family_partner_rel',   # même table de relation que dans res.partner
        'family_id',
        'partner_id',
        string='Membres de la famille'
    )
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
            family.email = family.partner_ids[:1].email if family.partner_ids else False

    def unlink(self):
        for family in self:
            if family.student_ids:
                noms_eleves = ", ".join(family.student_ids.mapped('display_name'))
                raise UserError(_(
                    "Impossible de supprimer la famille « %(name)s » : "
                    "elle est encore associée à %(count)d élève(s) (%(students)s).\n\n"
                    "Veuillez d'abord retirer ou réaffecter ces élèves à une autre "
                    "famille, ou contactez l'administration de l'école si vous "
                    "pensez qu'il s'agit d'une erreur."
                ) % {
                    'name': family.name,
                    'count': len(family.student_ids),
                    'students': noms_eleves,
                })
        return super().unlink()

    # Méthode pour générer un token (dans le contrôleur)