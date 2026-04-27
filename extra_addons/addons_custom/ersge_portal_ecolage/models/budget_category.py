# ersge_budget_category.py
from odoo import models, fields


class ErsgebBudgetCategory(models.Model):
    _name = "ersge.budget.category"
    _description = "Catégorie de budget familial"
    _order = "sequence, id"

    name = fields.Char(string="Catégorie", required=True)
    type = fields.Selection(
        [("income", "Revenu"), ("expense", "Charge")],
        string="Type",
        required=True,
    )
    include_in_totals = fields.Boolean(string="Inclure dans les totaux", default=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
