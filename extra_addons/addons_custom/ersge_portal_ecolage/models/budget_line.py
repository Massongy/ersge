from odoo import models, fields, api


class ErsgebBudgetLine(models.Model):
    _name = "ersge.budget.line"
    _description = "Ligne budget mensuel"
    _order = "category_id"

    dossier_id = fields.Many2one(
        "ersge.dossier.famille",
        string="Dossier",
        required=True,
        ondelete="cascade",
    )
    category_id = fields.Many2one(
        "ersge.budget.category",
        string="Catégorie",
        required=True,
        ondelete="restrict",
    )
    # Dénormalisés depuis la catégorie — stockés pour les domains et computes
    type = fields.Selection(
        [("income", "Revenu"), ("expense", "Charge")],
        related="category_id.type",
        store=True,
        readonly=True,
    )
    include_in_totals = fields.Boolean(
        related="category_id.include_in_totals",
        store=True,
        readonly=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        related="dossier_id.currency_id",
        store=True,
    )
    montant_monsieur = fields.Monetary(
        string="Monsieur",
        currency_field="currency_id",
        default=0.0,
    )
    montant_madame = fields.Monetary(
        string="Madame",
        currency_field="currency_id",
        default=0.0,
    )
    total_ligne = fields.Monetary(
        string="Total ligne",
        compute="_compute_total_ligne",
        store=True,
        currency_field="currency_id",
    )

    @api.depends("montant_monsieur", "montant_madame")
    def _compute_total_ligne(self):
        for line in self:
            line.total_ligne = (line.montant_monsieur or 0.0) + (
                line.montant_madame or 0.0
            )
