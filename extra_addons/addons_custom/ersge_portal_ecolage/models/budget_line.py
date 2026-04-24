from odoo import models, fields, api


class BudgetLine(models.Model):
    _name = "ersge.budget.line"
    _description = "Ligne budget mensuel"

    dossier_id = fields.Many2one(
        "ersge.dossier.famille", string="Dossier", required=True, ondelete="cascade"
    )
    category = fields.Char(string="Catégorie", required=False)
    description = fields.Char(string="Description")
    type = fields.Selection(
        [
            ("income", "Revenu"),
            ("expense", "Charge"),
        ],
        string="Type",
        required=True,
        default="expense",
    )
    include_in_totals = fields.Boolean(string="Inclure dans les totaux", default=True)

    # Nouveaux champs pour les deux colonnes
    montant_monsieur = fields.Monetary(string="Monsieur", currency_field="currency_id")
    montant_madame = fields.Monetary(string="Madame", currency_field="currency_id")
    currency_id = fields.Many2one(
        "res.currency", related="dossier_id.currency_id", store=True
    )

    # Champ calculé (optionnel) pour avoir un total par ligne
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
