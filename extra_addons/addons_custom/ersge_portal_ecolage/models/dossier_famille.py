# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import datetime

_logger = logging.getLogger(__name__)


class DossierFamille(models.Model):
    _name = "ersge.dossier.famille"
    _description = "Dossier d'engagement financier annuel"
    _rec_name = "display_name"
    _order = "date_soumission desc, id desc"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    # === IDENTIFICATION ===
    name = fields.Char(
        string="Référence", required=True, default="New", copy=False, readonly=True
    )
    annee_scolaire = fields.Char(
        string="Année scolaire",
        required=True,
        default=lambda self: self._get_current_school_year(),
    )
    display_name = fields.Char(compute="_compute_display_name", store=True)
    date_soumission = fields.Datetime(string="Date de soumission", readonly=True)

    # === LIEN PRINCIPAL ===
    family_id = fields.Many2one(
        "ersge.family", string="Famille", required=False, ondelete="restrict"
    )

    # === PREFILL ===
    prefilled_from_previous = fields.Boolean(default=False)
    prefilled_info = fields.Html(
        string="Données pré-remplies", compute="_compute_prefilled_info", store=False
    )

    # === WORKFLOW ===
    state = fields.Selection(
        [
            ("incomplet", "Incomplet"),
            ("soumis", "Soumis"),
            ("en_cours", "En cours de traitement"),
            ("complement", "Complément demandé"),
            ("valide", "Validé"),
            ("refuse", "Refusé"),
        ],
        string="Statut",
        default="incomplet",
    )
    allow_reopen = fields.Boolean(default=False)
    reopened_by = fields.Many2one("res.users", string="Réouvert par")
    reopened_date = fields.Datetime(string="Date de réouverture")

    # === REPRÉSENTATION LÉGALE ===
    legal_representation = fields.Selection(
        [
            ("both", "Père et Mère ayant la pleine autorité parentale"),
            ("mother_only", "Mère ayant seule la pleine autorité parentale"),
            ("father_only", "Père ayant seul la pleine autorité parentale"),
            ("other", "Autre"),
        ],
        string="Représentation légale",
        required=False,
        default="both",
    )
    legal_representation_other = fields.Char(
        string="Autre, précisez (ce champ ne peut pas être vide):"
    )

    # === COTISATION ===
    membership_fee_amount = fields.Monetary(
        string="Total Cotisation",
        readonly=True,
        currency_field="currency_id",
        compute="_compute_membership_fee_amount",
        store=True,
    )

    # === PARENTS ===
    parent1_id = fields.Many2one("res.partner", string="Parent 1", ondelete="restrict")
    parent1_firstname = fields.Char(
        string="Prénom", related="parent1_id.firstname", readonly=False, store=True
    )
    parent1_lastname = fields.Char(
        string="Nom", related="parent1_id.lastname", readonly=False, store=True
    )
    parent1_email = fields.Char(
        string="Email", related="parent1_id.email", readonly=False, store=True
    )
    parent1_phone = fields.Char(
        string="Téléphone mobile",
        related="parent1_id.phone",
        readonly=False,
        store=True,
    )
    parent1_phone_fixed = fields.Char(
        string="Téléphone fixe",
        related="parent1_id.phone_fixed",
        readonly=False,
        store=True,
    )
    parent1_phone_pro = fields.Char(
        string="Téléphone pro",
        related="parent1_id.phone_pro",
        readonly=False,
        store=True,
    )
    parent1_street = fields.Char(
        string="Adresse", related="parent1_id.street", readonly=False, store=True
    )
    parent1_zip = fields.Char(
        string="Code Postal", related="parent1_id.zip", readonly=False, store=True
    )
    parent1_city = fields.Char(
        string="Ville", related="parent1_id.city", readonly=False, store=True
    )
    parent1_country_id = fields.Many2one(
        "res.country",
        string="Pays",
        related="parent1_id.country_id",
        readonly=False,
        store=True,
    )
    parent1_profession = fields.Char(string="Profession")
    parent1_employeur = fields.Char(string="Employeur")

    parent2_id = fields.Many2one("res.partner", string="Parent 2", ondelete="restrict")
    same_address_as_parent1 = fields.Boolean(default=False)
    parent2_firstname = fields.Char(
        string="Prénom", related="parent2_id.firstname", readonly=False, store=True
    )
    parent2_lastname = fields.Char(
        string="Nom", related="parent2_id.lastname", readonly=False, store=True
    )
    parent2_email = fields.Char(
        string="Email", related="parent2_id.email", readonly=False, store=True
    )
    parent2_phone = fields.Char(
        string="Téléphone mobile",
        related="parent2_id.phone",
        readonly=False,
        store=True,
    )
    parent2_phone_fixed = fields.Char(
        string="Téléphone fixe",
        related="parent2_id.phone_fixed",
        readonly=False,
        store=True,
    )
    parent2_phone_pro = fields.Char(
        string="Téléphone pro",
        related="parent2_id.phone_pro",
        readonly=False,
        store=True,
    )
    parent2_street = fields.Char(
        string="Adresse", related="parent2_id.street", readonly=False, store=True
    )
    parent2_zip = fields.Char(
        string="Code Postal", related="parent2_id.zip", readonly=False, store=True
    )
    parent2_city = fields.Char(
        string="Ville", related="parent2_id.city", readonly=False, store=True
    )
    parent2_country_id = fields.Many2one(
        "res.country",
        string="Pays",
        related="parent2_id.country_id",
        readonly=False,
        store=True,
    )
    parent2_profession = fields.Char(string="Profession")
    parent2_employeur = fields.Char(string="Employeur")

    # === CURRENCY ===
    currency_id = fields.Many2one(
        "res.currency",
        string="Devise",
        default=lambda self: self.env.company.currency_id,
    )

    # === ÉLÈVES ===
    student_line_ids = fields.One2many(
        "ersge.dossier.student.line", "dossier_id", string="Élèves"
    )

    # Totaux
    total_monthly_tuition = fields.Monetary(
        string="Total mensuel écolage",
        compute="_compute_total_monthly_tuition",
        store=True,
        currency_field="currency_id",
    )
    total_monthly_after_school = fields.Monetary(
        string="Total mensuel parascolaire",
        compute="_compute_total_monthly_after_school",
        store=True,
        currency_field="currency_id",
    )
    total_annual_tuition = fields.Monetary(
        string="Total annuel écolage",
        compute="_compute_total_monthly_tuition",
        store=True,
        currency_field="currency_id",
    )
    total_annual_after_school = fields.Monetary(
        string="Total annuel parascolaire",
        compute="_compute_total_monthly_after_school",
        store=True,
        currency_field="currency_id",
    )
    total_monthly = fields.Monetary(
        string="Total mensuel combiné",
        readonly=True,
        currency_field="currency_id",
        compute="_compute_total_combined",
        store=True,
    )
    total_annual = fields.Monetary(
        string="Total annuel global",
        readonly=True,
        currency_field="currency_id",
        compute="_compute_total_combined",
        store=True,
    )

    # Aide employeur
    employer_name = fields.Char(
        related="employer_id.name", string="Nom", readonly=False, store=False
    )
    employer_street = fields.Char(
        related="employer_id.street", string="Adresse", readonly=False, store=False
    )
    employer_zip = fields.Char(
        related="employer_id.zip", string="Code Postal", readonly=False, store=False
    )
    employer_city = fields.Char(
        related="employer_id.city", string="Ville", readonly=False, store=False
    )
    employer_country_id = fields.Many2one(
        "res.country",
        related="employer_id.country_id",
        string="Pays",
        readonly=False,
        store=False,
    )

    actual_children_count = fields.Integer(
        string="Nombre d'enfants inscrits",
        compute="_compute_actual_children_count",
        store=True,
    )

    # Réductions
    reduction_requested = fields.Boolean(
        string="Je sollicite une réduction", default=False
    )
    max_children_discount = fields.Float(
        string="Réduction max enfants (%)", compute="_compute_max_discounts"
    )
    apply_children_discount = fields.Boolean(
        string="Appliquer réduction enfants", default=True
    )
    seniority_years = fields.Selection(
        [
            ("5", "Moins de 6 ans"),
            ("6", "6 années"),
            ("7", "7 années"),
            ("8", "8 années"),
            ("9", "9 années"),
            ("10", "10 ans et plus"),
        ],
        string="Années d'ancienneté",
        default="5",
    )
    max_seniority_discount = fields.Float(
        string="Réduction max ancienneté (%)",
        compute="_compute_max_discounts",
        store=True,
    )
    apply_seniority_discount = fields.Boolean(
        string="Appliquer réduction ancienneté", default=True
    )
    max_total_discount = fields.Float(
        string="Réduction maximale totale (%)",
        compute="_compute_max_discounts",
        store=True,
    )
    requested_discount = fields.Float(string="Pourcentage sollicité (%)", default=0.0)

    monthly_fee_after_children = fields.Monetary(
        string="Total mensuel après rabais enfants",
        compute="_compute_discounted_fees",
        store=True,
        currency_field="currency_id",
    )
    monthly_fee_after_seniority = fields.Monetary(
        string="Total mensuel après rabais ancienneté",
        compute="_compute_discounted_fees",
        store=True,
        currency_field="currency_id",
    )
    monthly_fee_at_max = fields.Monetary(
        string="Total mensuel après rabais maximal",
        compute="_compute_discounted_fees",
        store=True,
        currency_field="currency_id",
    )
    monthly_fee_after_requested = fields.Monetary(
        string="Total mensuel après rabais sollicité",
        compute="_compute_discounted_fees",
        store=True,
        currency_field="currency_id",
    )
    base_monthly_fee = fields.Monetary(
        string="Total mensuel (hors réduction)",
        compute="_compute_base_monthly_fee",
        store=True,
        currency_field="currency_id",
    )

    # Réduction complémentaire
    additional_reduction_request = fields.Boolean(
        string="Demande réduction complémentaire", default=False
    )
    gross_annual_income = fields.Float(string="Revenu brut annuel familial (CHF)")
    additional_reduction_income_percentage = fields.Float(
        string="Pourcentage que représente le tarif sur votre revenu annuel familial brut",
        compute="_compute_income_percentage",
        store=True,
        widget="percentage",
    )
    proposed_monthly_amount = fields.Monetary(
        string="Montant mensuel proposé", currency_field="currency_id"
    )

    # Parascolaire
    after_school_request = fields.Selection(
        [("yes", "Oui"), ("no", "Non")], string="Demande parascolaire", default="no"
    )
    after_school_line_ids = fields.One2many(
        "ersge.after.school.line", "dossier_id", string="Activités parascolaires"
    )

    # Solidarité, sponsorship, etc.
    solidarity_request = fields.Selection([("yes", "Oui"), ("no", "Non")])
    solidarity_percentage = fields.Float()
    sponsorship_request = fields.Selection([("yes", "Oui"), ("no", "Non")])
    sponsorship_type = fields.Selection([("type1", "Type 1"), ("type2", "Type 2")])
    sponsorship_id = fields.Many2one("res.partner")
    multi_billing_request = fields.Boolean()
    billing_line_ids = fields.One2many(
        "ersge.billing.line", "dossier_id", string="Lignes de facturation"
    )

    membership_fee = fields.Selection([("paid", "Payé"), ("unpaid", "Non payé")])
    deposit_status = fields.Selection([("paid", "Payé"), ("unpaid", "Non payé")])
    deposit_amount = fields.Monetary(
        string="Total Dépôt",
        readonly=True,
        currency_field="currency_id",
        compute="_compute_deposit_amount",
        store=True,
    )
    payment_terms = fields.Selection([("monthly", "Mensuel"), ("annually", "Annuel")])
    address_book_optin = fields.Boolean()

    employer_assistance = fields.Selection(
        [("yes", "Oui"), ("no", "Non")], string="Aide employeur", default="no"
    )
    send_invoice_to_employer = fields.Boolean(string="Envoyer la facture à l'employeur")
    employer_id = fields.Many2one("res.partner", string="Employeur")

    excluded_fees_info = fields.Html(string="Frais non compris", readonly=True)

    # Documents
    explanatory_letter_text = fields.Text(
        string="Lettre explicative", help="Décrivez ici votre situation familiale"
    )
    explanatory_letter_attachment = fields.Binary()
    explanatory_letter_filename = fields.Char()
    explanatory_letter_status = fields.Selection(
        [("draft", "Brouillon"), ("received", "Reçu"), ("validated", "Validé")]
    )
    explanatory_letter_mode = fields.Selection(
        [("upload", "Télécharger un fichier"), ("write", "Écrire directement")],
        string="Mode de saisie",
        default="upload",
    )

    # Budget
    budget_line_ids = fields.One2many(
        "ersge.budget.line", "dossier_id", string="Budget"
    )
    budget_income_line_ids = fields.One2many(
        "ersge.budget.line",
        "dossier_id",
        string="Revenus",
        domain=[("type", "=", "income")],
    )
    budget_expense_line_ids = fields.One2many(
        "ersge.budget.line",
        "dossier_id",
        string="Charges",
        domain=[("type", "=", "expense")],
    )
    budget_attachment = fields.Binary()
    budget_attachment_filename = fields.Char()
    tax_notice_attachment = fields.Binary()
    tax_notice_filename = fields.Char()
    tax_notice_status = fields.Selection(
        [("draft", "Brouillon"), ("received", "Reçu"), ("validated", "Validé")]
    )
    tax_notice_date = fields.Date()
    payslip_ids = fields.Many2many("ir.attachment", string="Fiches de salaire")

    budget_method = fields.Selection(
        [
            (
                "upload",
                "Télécharger la grille de budget du document de demande de réduction d'écolage ci-dessus.",
            ),
            ("online", "Remplir en ligne"),
        ],
        string="Mode de saisie du budget",
        default="online",
    )

    # Totaux budget (par type)
    total_revenus_monsieur = fields.Monetary(
        string="Revenus Monsieur",
        currency_field="currency_id",
        compute="_compute_budget_totals",
        store=True,  # stocké pour la recherche et l'affichage rapide
    )
    total_revenus_madame = fields.Monetary(
        string="Revenus Madame",
        currency_field="currency_id",
        compute="_compute_budget_totals",
        store=True,
    )
    total_charges_monsieur = fields.Monetary(
        string="Charges Monsieur",
        currency_field="currency_id",
        compute="_compute_budget_totals",
        store=True,
    )
    total_charges_madame = fields.Monetary(
        string="Charges Madame",
        currency_field="currency_id",
        compute="_compute_budget_totals",
        store=True,
    )
    total_revenus = fields.Monetary(
        string="Total revenus",
        currency_field="currency_id",
        compute="_compute_budget_totals",
        store=True,
    )
    total_charges = fields.Monetary(
        string="Total charges",
        currency_field="currency_id",
        compute="_compute_budget_totals",
        store=True,
    )
    solde = fields.Monetary(
        string="Solde",
        currency_field="currency_id",
        compute="_compute_budget_totals",
        store=True,
    )
    # Signature & acceptation
    contract_accepted = fields.Boolean()
    convention_accepted = fields.Boolean()
    procedures_accepted = fields.Boolean()
    terms_accepted = fields.Boolean()
    signature = fields.Binary()
    signature_date = fields.Datetime()
    lpd_consent = fields.Boolean()
    lpd_consent_date = fields.Datetime()

    # Suivi
    reminder_sent_count = fields.Integer()
    last_reminder_date = fields.Datetime()
    notes_internes = fields.Text()
    comments = fields.Text()
    complement_request_motif = fields.Text()

    legal_notice = fields.Html(readonly=True)
    technical_contact = fields.Html(readonly=True)

    # -------------------------------------------------------------------------
    # Compute methods
    # -------------------------------------------------------------------------
    @api.depends(
        "budget_line_ids.montant_madame",
        "budget_line_ids.montant_monsieur",
        "budget_line_ids.type",
        "budget_line_ids.include_in_totals",
    )
    def _compute_budget_totals(self):
        for record in self:
            revenus_madame = revenus_monsieur = 0.0
            charges_madame = charges_monsieur = 0.0
            for line in record.budget_line_ids:
                if not line.include_in_totals:
                    continue
                if line.type == "income":
                    revenus_madame += line.montant_madame
                    revenus_monsieur += line.montant_monsieur
                elif line.type == "expense":
                    charges_madame += line.montant_madame
                    charges_monsieur += line.montant_monsieur
            record.total_revenus_madame = revenus_madame
            record.total_revenus_monsieur = revenus_monsieur
            record.total_revenus = revenus_madame + revenus_monsieur
            record.total_charges_madame = charges_madame
            record.total_charges_monsieur = charges_monsieur
            record.total_charges = charges_madame + charges_monsieur
            record.solde = (revenus_madame + revenus_monsieur) - (
                charges_madame + charges_monsieur
            )

    @api.depends("family_id", "annee_scolaire")
    def _compute_display_name(self):
        for record in self:
            if record.family_id and record.annee_scolaire:
                record.display_name = (
                    f"{record.family_id.name} - {record.annee_scolaire}"
                )
            else:
                record.display_name = record.name or "Nouveau dossier"

    @api.depends("prefilled_from_previous")
    def _compute_prefilled_info(self):
        for record in self:
            if record.prefilled_from_previous:
                record.prefilled_info = """
                <div class="alert alert-info" role="alert">
                    <i class="fa fa-info-circle"></i>
                    <strong>Données pré-remplies</strong><br/>
                    Les informations ci-dessus ont été automatiquement récupérées depuis votre dossier de l'année précédente.<br/>
                    Veuillez vérifier et mettre à jour les champs si nécessaire.
                </div>
                """
            else:
                record.prefilled_info = False

    @api.depends("student_line_ids.forfait_montant_mensuel")
    def _compute_total_monthly_tuition(self):
        for record in self:
            total = sum(
                line.forfait_montant_mensuel for line in record.student_line_ids
            )
            record.total_monthly_tuition = total
            record.total_annual_tuition = total * 12

    @api.depends("after_school_line_ids.montant_mensuel")
    def _compute_total_monthly_after_school(self):
        for record in self:
            total = sum(line.montant_mensuel for line in record.after_school_line_ids)
            record.total_monthly_after_school = total
            record.total_annual_after_school = total * 12

    @api.depends(
        "total_monthly_tuition",
        "total_monthly_after_school",
        "reduction_requested",
        "monthly_fee_after_requested",
    )
    def _compute_total_combined(self):
        for record in self:
            if record.reduction_requested:
                record.total_monthly = record.monthly_fee_after_requested
            else:
                record.total_monthly = (record.total_monthly_tuition or 0) + (
                    record.total_monthly_after_school or 0
                )
            record.total_annual = record.total_monthly * 12

    @api.depends("legal_representation")
    def _compute_membership_fee_amount(self):
        for record in self:
            if record.legal_representation == "both":
                record.membership_fee_amount = 60
            elif record.legal_representation in ("mother_only", "father_only", "other"):
                record.membership_fee_amount = 40
            else:
                record.membership_fee_amount = 0

    @api.depends("deposit_status")
    def _compute_deposit_amount(self):
        for record in self:
            if record.deposit_status == "paid":
                record.deposit_amount = 0
            elif record.deposit_status == "unpaid":
                record.deposit_amount = 1000
            else:
                record.deposit_amount = 0

    @api.depends(
        "student_line_ids",
        "student_line_ids.forfait_montant_mensuel",
        "after_school_line_ids.montant_mensuel",
    )
    def _compute_base_monthly_fee(self):
        for rec in self:
            tuition = sum(line.forfait_montant_mensuel for line in rec.student_line_ids)
            after_school = sum(
                line.montant_mensuel for line in rec.after_school_line_ids
            )
            rec.base_monthly_fee = tuition + after_school

    @api.depends(
        "base_monthly_fee",
        "max_children_discount",
        "max_seniority_discount",
        "apply_children_discount",
        "apply_seniority_discount",
        "requested_discount",
    )
    def _compute_discounted_fees(self):
        for rec in self:
            children_disc = (
                rec.max_children_discount if rec.apply_children_discount else 0.0
            )
            rec.monthly_fee_after_children = rec.base_monthly_fee * (
                1 - children_disc / 100.0
            )
            seniority_disc = (
                rec.max_seniority_discount if rec.apply_seniority_discount else 0.0
            )
            rec.monthly_fee_after_seniority = rec.base_monthly_fee * (
                1 - seniority_disc / 100.0
            )
            max_disc = rec.max_total_discount
            rec.monthly_fee_at_max = rec.base_monthly_fee * (1 - max_disc / 100.0)
            requested = (
                min(rec.requested_discount, max_disc)
                if rec.reduction_requested
                else 0.0
            )
            rec.monthly_fee_after_requested = rec.base_monthly_fee * (
                1 - requested / 100.0
            )

    @api.depends("student_line_ids", "seniority_years")
    def _compute_max_discounts(self):
        children_map = {1: 0.0, 2: 10.0, 3: 20.0, 4: 30.0}
        seniority_map = {"5": 0.0, "6": 2.0, "7": 4.0, "8": 6.0, "9": 8.0, "10": 10.0}
        for rec in self:
            nb = len(rec.student_line_ids)
            if nb > 4:
                nb = 4
            rec.max_children_discount = children_map.get(nb, 0.0)
            rec.max_seniority_discount = seniority_map.get(rec.seniority_years, 0.0)
            rec.max_total_discount = (
                rec.max_children_discount + rec.max_seniority_discount
            )

    @api.depends("student_line_ids")
    def _compute_actual_children_count(self):
        for record in self:
            record.actual_children_count = len(record.student_line_ids)

    @api.depends("gross_annual_income", "monthly_fee_after_requested")
    def _compute_income_percentage(self):
        for record in self:
            if record.gross_annual_income and record.monthly_fee_after_requested:
                monthly_fee_francs = record.monthly_fee_after_requested / 100
                annual_fee = monthly_fee_francs * 12
                record.additional_reduction_income_percentage = (
                    annual_fee / record.gross_annual_income
                ) * 100
            else:
                record.additional_reduction_income_percentage = 0.0

    # -------------------------------------------------------------------------
    # Constraints
    # -------------------------------------------------------------------------
    @api.constrains("requested_discount", "max_total_discount", "reduction_requested")
    def _check_requested_discount(self):
        for rec in self:
            if (
                rec.reduction_requested
                and rec.requested_discount > rec.max_total_discount + 0.01
            ):
                raise ValidationError(
                    "Le pourcentage sollicité ne peut pas dépasser la réduction maximale totale (%.2f%%)"
                    % rec.max_total_discount
                )

    # -------------------------------------------------------------------------
    # Utilitaires
    # -------------------------------------------------------------------------
    @api.model
    def _get_current_school_year(self):
        today = datetime.date.today()
        year = today.year
        return f"{year}-{year+1}"

    # -------------------------------------------------------------------------
    # default_get
    # -------------------------------------------------------------------------
    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)

        # Forcer budget_method à 'online' si absent
        if not defaults.get("budget_method"):
            defaults["budget_method"] = "online"
            _logger.warning("default_get: budget_method forcé à online")
        family_id = (
            self._context.get("default_family_id")
            or self._context.get("parent_id")
            or defaults.get("family_id")
        )
        _logger.warning(f"family_id = {family_id}")

        budget_lines = []
        dernier_dossier = None
        categories = self.env["ersge.budget.category"].search(
            [("active", "=", True)], order="sequence, id"
        )

        if family_id:
            dernier_dossier = self.search(
                [("family_id", "=", family_id)], order="id desc", limit=1
            )
            _logger.warning(
                f"dernier_dossier = {dernier_dossier.id if dernier_dossier else 'None'}"
            )

            if dernier_dossier:
                # --- Copie des parents ---
                defaults["parent1_firstname"] = dernier_dossier.parent1_firstname
                defaults["parent1_lastname"] = dernier_dossier.parent1_lastname
                defaults["parent1_email"] = dernier_dossier.parent1_email
                defaults["parent1_phone"] = dernier_dossier.parent1_phone
                defaults["parent1_phone_fixed"] = dernier_dossier.parent1_phone_fixed
                defaults["parent1_phone_pro"] = dernier_dossier.parent1_phone_pro
                defaults["parent1_street"] = dernier_dossier.parent1_street
                defaults["parent1_zip"] = dernier_dossier.parent1_zip
                defaults["parent1_city"] = dernier_dossier.parent1_city
                if dernier_dossier.parent1_country_id:
                    defaults["parent1_country_id"] = (
                        dernier_dossier.parent1_country_id.id
                    )
                defaults["parent1_profession"] = dernier_dossier.parent1_profession
                defaults["parent1_employeur"] = dernier_dossier.parent1_employeur

                defaults["parent2_firstname"] = dernier_dossier.parent2_firstname
                defaults["parent2_lastname"] = dernier_dossier.parent2_lastname
                defaults["parent2_email"] = dernier_dossier.parent2_email
                defaults["parent2_phone"] = dernier_dossier.parent2_phone
                defaults["parent2_phone_fixed"] = dernier_dossier.parent2_phone_fixed
                defaults["parent2_phone_pro"] = dernier_dossier.parent2_phone_pro
                defaults["parent2_street"] = dernier_dossier.parent2_street
                defaults["parent2_zip"] = dernier_dossier.parent2_zip
                defaults["parent2_city"] = dernier_dossier.parent2_city
                if dernier_dossier.parent2_country_id:
                    defaults["parent2_country_id"] = (
                        dernier_dossier.parent2_country_id.id
                    )
                defaults["parent2_profession"] = dernier_dossier.parent2_profession
                defaults["parent2_employeur"] = dernier_dossier.parent2_employeur
                defaults["same_address_as_parent1"] = (
                    dernier_dossier.same_address_as_parent1
                )

                # --- Copie des lignes budget depuis l'ancien dossier ---
                if dernier_dossier.budget_line_ids:
                    for line in dernier_dossier.budget_line_ids:
                        budget_lines.append(
                            (
                                0,
                                0,
                                {
                                    "category_id": line.category_id.id,
                                    "montant_monsieur": line.montant_monsieur,
                                    "montant_madame": line.montant_madame,
                                },
                            )
                        )
                    _logger.warning(f"Budget copié: {len(budget_lines)} lignes")

                # --- Copie des enfants (élèves) ---
                if dernier_dossier.student_line_ids:
                    student_lines = []
                    for line in dernier_dossier.student_line_ids:
                        student_lines.append(
                            (
                                0,
                                0,
                                {
                                    "student_id": line.student_id.id,
                                    "image_rights": line.image_rights,
                                    "classe": line.classe,
                                    "forfait_id": line.forfait_id.id,
                                },
                            )
                        )
                    defaults["student_line_ids"] = student_lines
                    _logger.warning(f"Enfants copiés: {len(student_lines)} lignes")

            # --- Création des lignes parascolaires (avec ou sans ancien dossier) ---
            if not defaults.get("after_school_line_ids"):
                students = self.env["ersge.student"].search(
                    [("family_id", "=", family_id)]
                )
                if students:
                    lines = []
                    for student in students:
                        lines.append(
                            (
                                0,
                                0,
                                {
                                    "student_id": student.id,
                                    "selected": False,
                                    "accueil_type": "jardin",  # valeur par défaut, ajustez selon votre besoin
                                },
                            )
                        )
                    defaults["after_school_line_ids"] = lines
                    _logger.warning(
                        f"Lignes parascolaires créées pour {len(lines)} élèves"
                    )

        # --- Si aucune ligne budget n'a été copiée, création à partir des catégories ---
        if not budget_lines and categories:
            for cat in categories:
                budget_lines.append(
                    (
                        0,
                        0,
                        {
                            "category_id": cat.id,
                            "montant_monsieur": 0.0,
                            "montant_madame": 0.0,
                        },
                    )
                )
            _logger.warning(
                f"Budget créé avec {len(budget_lines)} catégories (mode online)"
            )

        if budget_lines:
            defaults["budget_line_ids"] = budget_lines
            _logger.warning(
                f"default_get retourne {len(budget_lines)} lignes budget, type={type(budget_lines[0])}"
            )

        defaults["prefilled_from_previous"] = bool(dernier_dossier)
        return defaults

    # -------------------------------------------------------------------------
    # CRUD
    # -------------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        _logger.warning("=== METHODE CREATE EXECUTEE ===")
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("ersge.dossier.famille")
                    or "New"
                )
        records = super().create(vals_list)
        for record in records:
            # Création des partenaires parents (code inchangé, je le simule)
            # ... (ton code pour parent1_id, parent2_id) ...
            # Pour éviter de surcharger, je mets une version simplifiée, mais tu as déjà le code complet.
            # L'important est l'appel à _init_budget_lines ci-dessous
            if record.budget_method == "online":
                record._init_budget_lines()
        return records

    # -------------------------------------------------------------------------
    # Onchange methods
    # -------------------------------------------------------------------------

    @api.onchange("employer_assistance")
    def _onchange_employer_assistance(self):
        if self.employer_assistance == "no":
            self.send_invoice_to_employer = False
            self.employer_id = False

    @api.onchange("after_school_request")
    def _onchange_after_school_request(self):
        if self.after_school_request == "yes" and not self.after_school_line_ids:
            students = self.env["ersge.student"].search(
                [("family_id", "=", self.family_id.id)]
            )
            for student in students:
                self.update(
                    {
                        "after_school_line_ids": [
                            (0, 0, {"student_id": student.id, "selected": True})
                        ]
                    }
                )

    # -------------------------------------------------------------------------
    # Workflow actions
    # -------------------------------------------------------------------------
    def action_soumettre(self):
        for record in self:
            record.state = "soumis"
            record.date_soumission = fields.Datetime.now()

    def action_mettre_en_cours(self):
        self.write({"state": "en_cours"})

    def action_demander_complement(self):
        self.write({"state": "complement"})

    def action_valider(self):
        self.write({"state": "valide"})

    def action_refuser(self):
        self.write({"state": "refuse"})

    def action_rouvrir(self):
        self.write(
            {
                "state": "incomplet",
                "reopened_by": self.env.user.id,
                "reopened_date": fields.Datetime.now(),
            }
        )

    # -------------------------------------------------------------------------
    # Budget init
    # -------------------------------------------------------------------------
    def _init_budget_lines(self):
        if self.budget_line_ids:
            return
        categories = self.env["ersge.budget.category"].search(
            [("active", "=", True)], order="sequence, id"
        )
        if not categories:
            _logger.warning("Aucune catégorie de budget active trouvée.")
            return
        vals = [
            (
                0,
                0,
                {"category_id": cat.id, "montant_monsieur": 0.0, "montant_madame": 0.0},
            )
            for cat in categories
        ]
        self.write({"budget_line_ids": vals})

    def write(self, vals):
        if "budget_method" in vals:
            _logger.warning(
                f"[WRITE] budget_method = {vals['budget_method']} pour dossiers {self.ids}"
            )
        result = super().write(vals)
        if vals.get("budget_method") == "online":
            for record in self:
                record._init_budget_lines()
        return result


class ErsgebBudgetLine(models.Model):
    _name = "ersge.budget.line"
    _description = "Ligne budget mensuel"
    _order = "category_id"

    dossier_id = fields.Many2one(
        "ersge.dossier.famille", string="Dossier", required=True, ondelete="cascade"
    )
    category_id = fields.Many2one(
        "ersge.budget.category", string="Catégorie", required=True, ondelete="restrict"
    )
    type = fields.Selection(
        [("income", "Revenu"), ("expense", "Charge")],
        related="category_id.type",
        store=True,
        readonly=True,
    )
    include_in_totals = fields.Boolean(
        related="category_id.include_in_totals", store=True, readonly=True
    )
    currency_id = fields.Many2one(
        "res.currency", related="dossier_id.currency_id", store=True
    )
    montant_monsieur = fields.Monetary(
        string="Monsieur", currency_field="currency_id", default=0.0
    )
    montant_madame = fields.Monetary(
        string="Madame", currency_field="currency_id", default=0.0
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
