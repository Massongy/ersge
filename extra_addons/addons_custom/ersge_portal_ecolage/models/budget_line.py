import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class ErsgebBudgetLine(models.Model):
    _name = "ersge.budget.line"
    _description = "Ligne budget mensuel"
    _order = "category_id"

    dossier_id = fields.Many2one(
        "ersge.dossier.famille",
        string="Dossier",
        required=False,
        ondelete="cascade",
    )
    category_id = fields.Many2one(
        "ersge.budget.category",
        string="Catégorie",
        required=True,
        ondelete="restrict",
    )

    currency_id = fields.Many2one(
        "res.currency",
        compute="_compute_currency_id",
        store=True,
    )

    type = fields.Selection(
        [("income", "Revenu"), ("expense", "Charge")],
        compute="_compute_from_category",
        store=True,
        readonly=True,
    )
    include_in_totals = fields.Boolean(
        compute="_compute_from_category",
        store=True,
        readonly=True,
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

    @api.depends("dossier_id", "dossier_id.currency_id")
    def _compute_currency_id(self):
        default_currency = self.env.company.currency_id
        for line in self:
            line.currency_id = line.dossier_id.currency_id or default_currency

    @api.depends("category_id", "category_id.type", "category_id.include_in_totals")
    def _compute_from_category(self):
        for line in self:
            if line.category_id:
                line.type = line.category_id.type
                line.include_in_totals = line.category_id.include_in_totals
                _logger.warning(
                    f"_compute_from_category: category={line.category_id.name}, type={line.type}"
                )
            else:
                line.type = False
                line.include_in_totals = False
                _logger.warning("_compute_from_category: pas de category_id")
