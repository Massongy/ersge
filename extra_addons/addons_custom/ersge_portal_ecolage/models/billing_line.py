# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ErsgebillingLine(models.Model):
    _name = 'ersge.billing.line'
    _description = 'Répartition de facturation'

    dossier_id = fields.Many2one(
        'ersge.dossier.famille',
        string='Dossier',
        required=True,
        ondelete='cascade'
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Payeur',
        required=True
    )
    billing_type = fields.Selection([
        ('parent',    'Parent'),
        ('employer',  'Employeur'),
        ('godfather', 'Parrain'),
    ], string='Type', required=True)

    percentage = fields.Float(string='Pourcentage', default=100.0)
    invoice_id = fields.Many2one(
        'account.move',
        string='Facture générée',
        readonly=True
    )
    
    # ========== AJOUTEZ CES CHAMPS ==========
    montant_mensuel = fields.Monetary(
        string='Montant mensuel',
        compute='_compute_montants',
        store=True,
        currency_field='currency_id'
    )
    montant_annuel = fields.Monetary(
        string='Montant annuel',
        compute='_compute_montants',
        store=True,
        currency_field='currency_id'
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='dossier_id.currency_id',
        store=True
    )
    
    @api.depends('percentage', 'dossier_id.total_monthly')
    def _compute_montants(self):
        for record in self:
            total_mensuel = record.dossier_id.total_monthly or 0
            record.montant_mensuel = total_mensuel * (record.percentage / 100)
            record.montant_annuel = record.montant_mensuel * 12
    # ========================================

    @api.constrains('percentage')
    def _check_percentage(self):
        for record in self:
            # Éviter l'erreur si le dossier n'a pas encore de lignes
            if record.dossier_id and record.dossier_id.billing_line_ids:
                total = sum(record.dossier_id.billing_line_ids.mapped('percentage'))
                if total != 100.0:
                    raise ValidationError(
                        "La répartition de facturation doit totaliser 100%."
                    )