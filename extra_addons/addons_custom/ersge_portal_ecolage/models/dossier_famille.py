# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import datetime

class DossierFamille(models.Model):
    _name = 'ersge.dossier.famille'
    _description = "Dossier d'engagement financier annuel"
    _rec_name = 'display_name'
    _order = 'date_soumission desc, id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # === IDENTIFICATION ===
    name = fields.Char(string='Référence', required=True, default='New', copy=False, readonly=True)
    annee_scolaire = fields.Char(string='Année scolaire', required=True, default=lambda self: self._get_current_school_year())
    display_name = fields.Char(compute='_compute_display_name', store=True)
    date_soumission = fields.Datetime(string="Date de soumission", readonly=True)

    # === LIEN PRINCIPAL ===
    family_id = fields.Many2one('ersge.family', string='Famille', required=True, ondelete='restrict')

    # === PREFILL ===
    prefilled_from_previous = fields.Boolean(default=False)
    prefilled_info = fields.Html(string='Données pré-remplies', compute='_compute_prefilled_info', store=False)

    # === WORKFLOW ===
    state = fields.Selection([
        ('incomplet', 'Incomplet'),
        ('soumis', 'Soumis'),
        ('en_cours', 'En cours de traitement'),
        ('complement', 'Complément demandé'),
        ('valide', 'Validé'),
        ('refuse', 'Refusé'),
    ], string='Statut', default='incomplet')
    allow_reopen = fields.Boolean(default=False)
    reopened_by = fields.Many2one('res.users', string="Réouvert par")
    reopened_date = fields.Datetime(string="Date de réouverture")

    # === REPRÉSENTATION LÉGALE ===
    legal_representation = fields.Selection([
        ('both', 'Père et Mère ayant la pleine autorité parentale'),
        ('mother_only', 'Mère ayant seule la pleine autorité parentale'),
        ('father_only', 'Père ayant seul la pleine autorité parentale'),
        ('other', 'Autre')
    ], string="Représentation légale", required=True, default='both')
    legal_representation_other = fields.Char(string="Autre, précisez (ce champ ne peut pas être vide):")

    # === COTISATION ===
    membership_fee_amount = fields.Monetary(
        string="Total Cotisation", 
        readonly=True, 
        currency_field='currency_id',
        compute='_compute_membership_fee_amount',
        store=True
    )

    # === PARENTS ===
    parent1_id = fields.Many2one('res.partner', string="Parent 1", ondelete='restrict')
    parent1_firstname   = fields.Char(string='Prénom',               related='parent1_id.firstname',   readonly=False, store=False)
    parent1_lastname    = fields.Char(string='Nom',                  related='parent1_id.lastname',    readonly=False, store=False)
    parent1_email       = fields.Char(string='Email',                related='parent1_id.email',       readonly=False, store=False)
    parent1_phone       = fields.Char(string='Téléphone mobile',     related='parent1_id.phone',       readonly=False, store=False)
    parent1_phone_fixed = fields.Char(string='Téléphone fixe',       related='parent1_id.phone_fixed', readonly=False, store=False)
    parent1_phone_pro   = fields.Char(string='Téléphone pro',        related='parent1_id.phone_pro',   readonly=False, store=False)
    parent1_street      = fields.Char(string='Adresse',              related='parent1_id.street',      readonly=False, store=False)
    parent1_zip         = fields.Char(string='Code Postal',          related='parent1_id.zip',         readonly=False, store=False)
    parent1_city        = fields.Char(string='Ville',                related='parent1_id.city',        readonly=False, store=False)
    parent1_country_id  = fields.Many2one('res.country', string='Pays', related='parent1_id.country_id', readonly=False, store=False)
    parent1_profession  = fields.Char(string='Profession')
    parent1_employeur   = fields.Char(string='Employeur')

    parent2_id = fields.Many2one('res.partner', string="Parent 2", ondelete='restrict')
    same_address_as_parent1 = fields.Boolean(default=False)
    parent2_firstname   = fields.Char(string='Prénom',               related='parent2_id.firstname',   readonly=False, store=False)
    parent2_lastname    = fields.Char(string='Nom',                  related='parent2_id.lastname',    readonly=False, store=False)
    parent2_email       = fields.Char(string='Email',                related='parent2_id.email',       readonly=False, store=False)
    parent2_phone       = fields.Char(string='Téléphone mobile',     related='parent2_id.phone',       readonly=False, store=False)
    parent2_phone_fixed = fields.Char(string='Téléphone fixe',       related='parent2_id.phone_fixed', readonly=False, store=False)
    parent2_phone_pro   = fields.Char(string='Téléphone pro',        related='parent2_id.phone_pro',   readonly=False, store=False)
    parent2_street      = fields.Char(string='Adresse',              related='parent2_id.street',      readonly=False, store=False)
    parent2_zip         = fields.Char(string='Code Postal',          related='parent2_id.zip',         readonly=False, store=False)
    parent2_city        = fields.Char(string='Ville',                related='parent2_id.city',        readonly=False, store=False)
    parent2_country_id  = fields.Many2one('res.country', string='Pays', related='parent2_id.country_id', readonly=False, store=False)
    parent2_profession  = fields.Char(string='Profession')
    parent2_employeur   = fields.Char(string='Employeur')

    # === CURRENCY ===
    currency_id = fields.Many2one('res.currency', string='Devise', default=lambda self: self.env.company.currency_id)

    # === ÉLÈVES ===
    nb_students = fields.Integer(
        string="Nombre d'enfant(s) à inscrire",
        compute='_compute_nb_students',
        store=True
    )

    student_line_ids = fields.One2many('ersge.dossier.student.line', 'dossier_id', string="Élèves")

    # Totaux mensuels et annuels (avec compute)
    total_monthly_tuition = fields.Monetary(
        string="Total mensuel écolage",
        compute='_compute_total_monthly_tuition',
        store=True,
        currency_field='currency_id'
    )
    total_monthly_after_school = fields.Monetary(
        string="Total mensuel parascolaire",
        compute='_compute_total_monthly_after_school',
        store=True,
        currency_field='currency_id'
    )
    total_annual_tuition = fields.Monetary(
        string="Total annuel écolage",
        compute='_compute_total_monthly_tuition',
        store=True,
        currency_field='currency_id'
    )
    total_annual_after_school = fields.Monetary(
        string="Total annuel parascolaire",
        compute='_compute_total_monthly_after_school',
        store=True,
        currency_field='currency_id'
    )
    total_monthly = fields.Monetary(
        string="Total mensuel combiné",
        readonly=True,
        currency_field='currency_id',
        compute='_compute_total_combined',
        store=True
    )
    total_annual = fields.Monetary(
        string="Total annuel global",
        readonly=True,
        currency_field='currency_id',
        compute='_compute_total_combined',
        store=True
    )

    # === AIDE EMPLOYEUR ===
    employer_name   = fields.Char(related='employer_id.name',    string='Nom',         readonly=False, store=False)
    employer_street = fields.Char(related='employer_id.street',  string='Adresse',     readonly=False, store=False)
    employer_zip    = fields.Char(related='employer_id.zip',     string='Code Postal', readonly=False, store=False)
    employer_city   = fields.Char(related='employer_id.city',    string='Ville',       readonly=False, store=False)
    employer_country_id = fields.Many2one('res.country', related='employer_id.country_id', string='Pays', readonly=False, store=False)

    # === RÉDUCTIONS ===
    reduction_requested = fields.Boolean(string="Je sollicite une réduction", default=False)

    # Nombre d'enfants
    children_count = fields.Selection([
        ('1', '1 enfant'),
        ('2', '2 enfants'),
        ('3', '3 enfants'),
        ('4', '4 enfants et plus'),
    ], string="Nombre d'enfants inscrits", default='1')
    max_children_discount = fields.Float(string="Réduction max enfants (%)", compute='_compute_max_discounts', store=True)
    apply_children_discount = fields.Boolean(string="Appliquer réduction enfants", default=True)

    # Ancienneté
    seniority_years = fields.Selection([
        ('5', 'Moins de 6 ans'),
        ('6', '6 années'),
        ('7', '7 années'),
        ('8', '8 années'),
        ('9', '9 années'),
        ('10', '10 ans et plus'),
    ], string="Années d'ancienneté", default='5')
    max_seniority_discount = fields.Float(string="Réduction max ancienneté (%)", compute='_compute_max_discounts', store=True)
    apply_seniority_discount = fields.Boolean(string="Appliquer réduction ancienneté", default=True)

    # Ajustement
    max_total_discount = fields.Float(string="Réduction maximale totale (%)", compute='_compute_max_discounts', store=True)
    requested_discount = fields.Float(string="Pourcentage sollicité (%)", default=0.0)

    # Montants calculés après réduction
    monthly_fee_after_children = fields.Monetary(string="Total mensuel après rabais enfants", compute='_compute_discounted_fees', store=True, currency_field='currency_id')
    monthly_fee_after_seniority = fields.Monetary(string="Total mensuel après rabais ancienneté", compute='_compute_discounted_fees', store=True, currency_field='currency_id')
    monthly_fee_at_max = fields.Monetary(string="Total mensuel après rabais max", compute='_compute_discounted_fees', store=True, currency_field='currency_id')
    monthly_fee_after_requested = fields.Monetary(string="Total mensuel après rabais sollicité", compute='_compute_discounted_fees', store=True, currency_field='currency_id')

    # Base mensuelle (hors réduction)
    base_monthly_fee = fields.Monetary(string="Base mensuelle (hors réduction)", compute='_compute_base_monthly_fee', store=True, currency_field='currency_id')

    # === RÉDUCTION COMPLÉMENTAIRE ===
    additional_reduction_request = fields.Boolean(string="Demande réduction complémentaire", default=False)
    additional_reduction_income_percentage = fields.Float(string="Pourcentage du revenu")
    annual_gross_income = fields.Monetary(string="Revenu annuel brut", currency_field='currency_id')
    proposed_monthly_amount = fields.Monetary(string="Montant mensuel proposé", currency_field='currency_id')
    
    # === PARASCOLAIRE ===
    after_school_request = fields.Selection([('yes','Oui'),('no','Non')], string="Demande parascolaire")
    after_school_line_ids = fields.One2many('ersge.after.school.line','dossier_id', string="Activités parascolaires")

    # === SOLIDARITÉ / SPONSORSHIP ===
    solidarity_request = fields.Selection([('yes','Oui'),('no','Non')])
    solidarity_percentage = fields.Float()
    sponsorship_request = fields.Selection([('yes','Oui'),('no','Non')])
    sponsorship_type = fields.Selection([('type1','Type 1'),('type2','Type 2')])
    sponsorship_id = fields.Many2one('res.partner')
    multi_billing_request = fields.Boolean()
    billing_line_ids = fields.One2many('ersge.billing.line','dossier_id', string="Lignes de facturation")

    membership_fee = fields.Selection([('paid','Payé'),('unpaid','Non payé')])
    deposit_status = fields.Selection([('paid','Payé'),('unpaid','Non payé')])
    deposit_amount = fields.Monetary(
        string="Total Dépôt",
        readonly=True,
        currency_field='currency_id',
        compute='_compute_deposit_amount',
        store=True
    )    
    payment_terms = fields.Selection([('monthly','Mensuel'),('annually','Annuel')])
    address_book_optin = fields.Boolean()

    # === AIDE EMPLOYEUR ===
    employer_assistance = fields.Selection([
        ('yes', 'Oui'),
        ('no', 'Non')
    ], string="Aide employeur", default='no')
    send_invoice_to_employer = fields.Boolean(string="Envoyer la facture à l'employeur")
    employer_id = fields.Many2one('res.partner', string="Employeur")
    
    # === FRAIS NON COMPRIS ===
    excluded_fees_info = fields.Html(string="Frais non compris", readonly=True)

    # === DOCUMENTS ET ATTACHEMENTS ===
    explanatory_letter_text = fields.Text()
    explanatory_letter_attachment = fields.Binary()
    explanatory_letter_filename = fields.Char()
    explanatory_letter_status = fields.Selection([('draft','Brouillon'),('received','Reçu'),('validated','Validé')])

    # Budget

    
            
    budget_line_ids = fields.One2many('ersge.budget.line','dossier_id')
    budget_income_line_ids = fields.One2many(
        'ersge.budget.line', 'dossier_id',
        domain=[('type', '=', 'income')],
        string='Revenus'
    )

    budget_expense_line_ids = fields.One2many(
        'ersge.budget.line', 'dossier_id',
        domain=[('type', '=', 'expense')],
        string='Charges'
    )
    budget_attachment = fields.Binary()
    budget_attachment_filename = fields.Char()

    tax_notice_attachment = fields.Binary()
    tax_notice_filename = fields.Char()
    tax_notice_status = fields.Selection([('draft','Brouillon'),('received','Reçu'),('validated','Validé')])
    tax_notice_date = fields.Date()

    payslip_ids = fields.Many2many(
        'ir.attachment',
        string="Fiches de salaire",
        help="Vous pouvez télécharger plusieurs fichiers (max 8MB)"
    )

    budget_method = fields.Selection([
        ('upload', 'Télécharger un document'),
        ('online', 'Remplir en ligne')
    ], string="Mode de saisie du budget", default='upload')

    # Totaux budget (par type et par colonne)
    total_revenus_monsieur = fields.Monetary(
        string="Revenus Monsieur",
        compute='_compute_budget_totals',
        currency_field='currency_id'
    )
    total_revenus_madame = fields.Monetary(
        string="Revenus Madame",
        compute='_compute_budget_totals',
        currency_field='currency_id'
    )
    total_charges_monsieur = fields.Monetary(
        string="Charges Monsieur",
        compute='_compute_budget_totals',
        currency_field='currency_id'
    )
    total_charges_madame = fields.Monetary(
        string="Charges Madame",
        compute='_compute_budget_totals',
        currency_field='currency_id'
    )
    total_revenus = fields.Monetary(
        string="Total revenus",
        compute='_compute_budget_totals',
        currency_field='currency_id'
    )
    total_charges = fields.Monetary(
        string="Total charges",
        compute='_compute_budget_totals',
        currency_field='currency_id'
    )
    solde = fields.Monetary(
        string="Solde",
        compute='_compute_budget_totals',
        currency_field='currency_id'
    )
    def action_save_budget(self):
            for line in self.budget_income_line_ids:
                line.write({
                    'montant_monsieur': line.montant_monsieur,
                    'montant_madame': line.montant_madame,
                })
            for line in self.budget_expense_line_ids:
                line.write({
                    'montant_monsieur': line.montant_monsieur,
                    'montant_madame': line.montant_madame,
                })
                
    def _ensure_budget_lines(self):
        if self.budget_method != 'online':
            return
        existing = self.env['ersge.budget.line'].search([('dossier_id', '=', self.id)])
        if not existing:
            categories = [
                ("Salaire brut (indiquez svp aussi le net entre parenthèses)", "income", True),
                ("dont Salaire net (à titre indicatif)", "income", False),
                ("Allocations familiales", "income", True),
                ("Pension alimentaire (reçue)", "income", True),
                ("Autres revenus", "income", True),
                ("Fortune (immobilière, etc)", "income", True),
                ("Logement", "expense", True),
                ("Impôts", "expense", True),
                ("Assurance-maladie", "expense", True),
                ("Frais médicaux non remboursés (lunette, dentiste, etc)", "expense", True),
                ("Autres assurances (ménage, voiture)", "expense", True),
                ("Energie (gaz, électricité, etc)", "expense", True),
                ("Télécommunications (TV, internet, fixe, mobile, etc)", "expense", True),
                ("Alimentation", "expense", True),
                ("Pension alimentaire (versée)", "expense", True),
                ("Transports (bus, voiture, scooter)", "expense", True),
                ("Vêtements", "expense", True),
                ("Ecolage (École Rudolf Steiner)", "expense", True),
                ("Activités extrascolaires (musique, sport, etc)", "expense", True),
                ("Cadeaux", "expense", True),
                ("Argent de poche enfants", "expense", True),
                ("Formations", "expense", True),
                ("Loisirs – vacances", "expense", True),
                ("Dettes (carte crédit, autres)", "expense", True),
                ("Autre :", "expense", True),
                ("Autre :", "expense", True),
            ]
            for cat, typ, include in categories:
                self.env['ersge.budget.line'].create({
                    'dossier_id': self.id,
                    'category': cat,
                    'type': typ,
                    'include_in_totals': include,
                    'montant_monsieur': 0.0,
                    'montant_madame': 0.0,
                })

    # === SIGNATURE & ACCEPTATION ===
    contract_accepted = fields.Boolean()
    convention_accepted = fields.Boolean()
    procedures_accepted = fields.Boolean()
    terms_accepted = fields.Boolean()
    signature = fields.Binary()
    signature_date = fields.Datetime()
    lpd_consent = fields.Boolean()
    lpd_consent_date = fields.Datetime()

    # === SUIVI & WORKFLOW ===
    reminder_sent_count = fields.Integer()
    last_reminder_date = fields.Datetime()
    notes_internes = fields.Text()
    comments = fields.Text()
    complement_request_motif = fields.Text()

    # Mentions légales
    legal_notice = fields.Html(readonly=True)
    technical_contact = fields.Html(readonly=True)

    # -------------------------------------------------------------------------
    # COMPUTE METHODS
    # -------------------------------------------------------------------------

    @api.depends('family_id', 'annee_scolaire')
    def _compute_display_name(self):
        for record in self:
            if record.family_id and record.annee_scolaire:
                record.display_name = f"{record.family_id.name} - {record.annee_scolaire}"
            else:
                record.display_name = record.name or "Nouveau dossier"

    @api.depends('prefilled_from_previous')
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

    @api.depends('student_line_ids')
    def _compute_nb_students(self):
        for record in self:
            record.nb_students = len(record.student_line_ids)

    @api.depends('student_line_ids.forfait_montant_mensuel')
    def _compute_total_monthly_tuition(self):
        for record in self:
            total = sum(line.forfait_montant_mensuel for line in record.student_line_ids)
            record.total_monthly_tuition = total
            record.total_annual_tuition = total * 12

    @api.depends('after_school_line_ids.montant_mensuel')
    def _compute_total_monthly_after_school(self):
        for record in self:
            total = sum(line.montant_mensuel for line in record.after_school_line_ids)
            record.total_monthly_after_school = total
            record.total_annual_after_school = total * 12

    @api.depends('total_monthly_tuition', 'total_monthly_after_school', 'reduction_requested', 'monthly_fee_after_requested')
    def _compute_total_combined(self):
        for record in self:
            if record.reduction_requested:
                record.total_monthly = record.monthly_fee_after_requested
            else:
                record.total_monthly = (record.total_monthly_tuition or 0) + (record.total_monthly_after_school or 0)
            record.total_annual = record.total_monthly * 12

    @api.depends('legal_representation')
    def _compute_membership_fee_amount(self):
        for record in self:
            if record.legal_representation == 'both':
                record.membership_fee_amount = 60
            elif record.legal_representation in ('mother_only', 'father_only', 'other'):
                record.membership_fee_amount = 40
            else:
                record.membership_fee_amount = 0

    @api.depends('deposit_status')
    def _compute_deposit_amount(self):
        for record in self:
            if record.deposit_status == 'paid':
                record.deposit_amount = 0
            elif record.deposit_status == 'unpaid':
                record.deposit_amount = 1000
            else:
                record.deposit_amount = 0

    # --- Réductions ---
    @api.depends('children_count', 'seniority_years')
    def _compute_max_discounts(self):
        children_map = {'1': 0.0, '2': 10.0, '3': 20.0, '4': 30.0}
        seniority_map = {'5': 0.0, '6': 2.0, '7': 4.0, '8': 6.0, '9': 8.0, '10': 10.0}
        for rec in self:
            rec.max_children_discount = children_map.get(rec.children_count, 0.0)
            rec.max_seniority_discount = seniority_map.get(rec.seniority_years, 0.0)
            rec.max_total_discount = rec.max_children_discount + rec.max_seniority_discount

    @api.depends('student_line_ids', 'student_line_ids.forfait_montant_mensuel', 'after_school_line_ids.montant_mensuel')
    def _compute_base_monthly_fee(self):
        for rec in self:
            tuition = sum(line.forfait_montant_mensuel for line in rec.student_line_ids)
            after_school = sum(line.montant_mensuel for line in rec.after_school_line_ids)
            rec.base_monthly_fee = tuition + after_school

    @api.depends('base_monthly_fee', 'max_children_discount', 'max_seniority_discount',
                 'apply_children_discount', 'apply_seniority_discount', 'requested_discount')
    def _compute_discounted_fees(self):
        for rec in self:
            children_disc = rec.max_children_discount if rec.apply_children_discount else 0.0
            rec.monthly_fee_after_children = rec.base_monthly_fee * (1 - children_disc / 100.0)
            seniority_disc = rec.max_seniority_discount if rec.apply_seniority_discount else 0.0
            rec.monthly_fee_after_seniority = rec.base_monthly_fee * (1 - seniority_disc / 100.0)
            max_disc = rec.max_total_discount
            rec.monthly_fee_at_max = rec.base_monthly_fee * (1 - max_disc / 100.0)
            requested = min(rec.requested_discount, max_disc) if rec.reduction_requested else 0.0
            rec.monthly_fee_after_requested = rec.base_monthly_fee * (1 - requested / 100.0)

    @api.depends(
        'budget_line_ids.montant_monsieur', 
        'budget_line_ids.montant_madame', 
        'budget_line_ids.type', 
        'budget_line_ids.include_in_totals',
        'budget_income_line_ids.montant_monsieur',
        'budget_income_line_ids.montant_madame',
        'budget_expense_line_ids.montant_monsieur',
        'budget_expense_line_ids.montant_madame',
    )
    def _compute_budget_totals(self):
        for rec in self:
            revenus_m = sum(line.montant_monsieur for line in rec.budget_line_ids if line.type == 'income' and line.include_in_totals)
            revenus_f = sum(line.montant_madame for line in rec.budget_line_ids if line.type == 'income' and line.include_in_totals)
            charges_m = sum(line.montant_monsieur for line in rec.budget_line_ids if line.type == 'expense' and line.include_in_totals)
            charges_f = sum(line.montant_madame for line in rec.budget_line_ids if line.type == 'expense' and line.include_in_totals)
            rec.total_revenus_monsieur = revenus_m
            rec.total_revenus_madame = revenus_f
            rec.total_charges_monsieur = charges_m
            rec.total_charges_madame = charges_f
            rec.total_revenus = revenus_m + revenus_f
            rec.total_charges = charges_m + charges_f
            rec.solde = rec.total_revenus - rec.total_charges

    # -------------------------------------------------------------------------
    # CONSTRAINTS
    # -------------------------------------------------------------------------
    @api.constrains('requested_discount', 'max_total_discount', 'reduction_requested')
    def _check_requested_discount(self):
        for rec in self:
            if rec.reduction_requested and rec.requested_discount > rec.max_total_discount + 0.01:
                raise ValidationError("Le pourcentage sollicité ne peut pas dépasser la réduction maximale totale (%.2f%%)" % rec.max_total_discount)

    # -------------------------------------------------------------------------
    # UTILITAIRES
    # -------------------------------------------------------------------------
    @api.model
    def _get_current_school_year(self):
        today = datetime.date.today()
        year = today.year
        if today.month >= 8:
            return f"{year}-{year+1}"
        return f"{year-1}-{year}"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('ersge.dossier.famille') or 'New'
        records = super().create(vals_list)
        # Création des lignes budget si nécessaire (après création)
        for record in records:
            record._ensure_budget_lines()
        return records

    def write(self, vals):
        result = super().write(vals)
        for record in self:
            record._ensure_budget_lines()
            record.student_line_ids._create_student_if_needed(record)
        return result

    # -------------------------------------------------------------------------
    # ACTIONS WORKFLOW
    # -------------------------------------------------------------------------
    def action_soumettre(self):
        for record in self:
            record.state = 'soumis'
            record.date_soumission = fields.Datetime.now()

    def action_mettre_en_cours(self):
        for record in self:
            record.state = 'en_cours'

    def action_demander_complement(self):
        for record in self:
            record.state = 'complement'

    def action_valider(self):
        for record in self:
            record.state = 'valide'

    def action_refuser(self):
        for record in self:
            record.state = 'refuse'

    def action_rouvrir(self):
        for record in self:
            record.state = 'incomplet'
            record.reopened_by = self.env.user
            record.reopened_date = fields.Datetime.now()

    @api.onchange('employer_assistance')
    def _onchange_employer_assistance(self):
        if self.employer_assistance == 'no':
            self.send_invoice_to_employer = False
            self.employer_id = False

    # ========================================================================
    # AJOUT : onchange pour créer les lignes budget dès le basculement en mode "online"
    # ========================================================================
    @api.onchange('budget_method')
    def _onchange_budget_method(self):
        if self.budget_method == 'online' and not self.budget_line_ids:
            categories = [
                ("Salaire brut (indiquez svp aussi le net entre parenthèses)", "income", True),
                ("dont Salaire net (à titre indicatif)", "income", False),
                ("Allocations familiales", "income", True),
                ("Pension alimentaire (reçue)", "income", True),
                ("Autres revenus", "income", True),
                ("Fortune (immobilière, etc)", "income", True),
                ("Logement", "expense", True),
                ("Impôts", "expense", True),
                ("Assurance-maladie", "expense", True),
                ("Frais médicaux non remboursés (lunette, dentiste, etc)", "expense", True),
                ("Autres assurances (ménage, voiture)", "expense", True),
                ("Energie (gaz, électricité, etc)", "expense", True),
                ("Télécommunications (TV, internet, fixe, mobile, etc)", "expense", True),
                ("Alimentation", "expense", True),
                ("Pension alimentaire (versée)", "expense", True),
                ("Transports (bus, voiture, scooter)", "expense", True),
                ("Vêtements", "expense", True),
                ("Ecolage (École Rudolf Steiner)", "expense", True),
                ("Activités extrascolaires (musique, sport, etc)", "expense", True),
                ("Cadeaux", "expense", True),
                ("Argent de poche enfants", "expense", True),
                ("Formations", "expense", True),
                ("Loisirs – vacances", "expense", True),
                ("Dettes (carte crédit, autres)", "expense", True),
                ("Autre :", "expense", True),
                ("Autre :", "expense", True),
            ]
            vals = [
                (0, 0, {
                    'category': cat,
                    'type': typ,
                    'include_in_totals': include,
                    'montant_monsieur': 0.0,
                    'montant_madame': 0.0,
                }) for cat, typ, include in categories
            ]
            self.budget_line_ids = vals
        # Forcer les champs filtrés depuis les lignes en mémoire
        self.budget_income_line_ids = self.budget_line_ids.filtered(lambda l: l.type == 'income')
        self.budget_expense_line_ids = self.budget_line_ids.filtered(lambda l: l.type == 'expense')
    @api.onchange('budget_line_ids')
    def _onchange_budget_line_ids(self):
        # Force Odoo à recalculer les vues filtrées
        self.budget_income_line_ids = self.budget_line_ids.filtered(lambda l: l.type == 'income')
        self.budget_expense_line_ids = self.budget_line_ids.filtered(lambda l: l.type == 'expense')
    @api.onchange('budget_income_line_ids', 'budget_expense_line_ids')
    def _onchange_budget_lines_totals(self):
        revenus_m = sum(line.montant_monsieur for line in self.budget_income_line_ids if line.include_in_totals)
        revenus_f = sum(line.montant_madame for line in self.budget_income_line_ids if line.include_in_totals)
        charges_m = sum(line.montant_monsieur for line in self.budget_expense_line_ids if line.include_in_totals)
        charges_f = sum(line.montant_madame for line in self.budget_expense_line_ids if line.include_in_totals)
        self.total_revenus_monsieur = revenus_m
        self.total_revenus_madame = revenus_f
        self.total_charges_monsieur = charges_m
        self.total_charges_madame = charges_f
        self.total_revenus = revenus_m + revenus_f
        self.total_charges = charges_m + charges_f
        self.solde = self.total_revenus - self.total_charges

    @api.onchange('after_school_request')
    def _onchange_after_school_request(self):
        if self.after_school_request == 'yes' and not self.after_school_line_ids:
            students = self.env['ersge.student'].search([('family_id', '=', self.family_id.id)])
            for student in students:
                self.update({
                    'after_school_line_ids': [(0, 0, {
                        'student_id': student.id,
                        'selected': True,
                    })]
                })