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

    total_monthly_tuition = fields.Monetary(string="Total mensuel écolage", readonly=True, currency_field='currency_id')
    total_monthly_after_school = fields.Monetary(
        string="Total mensuel parascolaire",
        readonly=True,
        currency_field='currency_id',
        compute='_compute_total_after_school',
        store=True
    )
    total_monthly = fields.Monetary(
        string="Total mensuel combiné",
        readonly=True,
        currency_field='currency_id',
        compute='_compute_total_combined',
        store=True
    )
    total_annual_tuition = fields.Monetary(string="Total annuel écolage", readonly=True, currency_field='currency_id')
    total_annual_after_school = fields.Monetary(
        string="Total annuel parascolaire",
        readonly=True,
        currency_field='currency_id',
        compute='_compute_total_after_school',
        store=True
    )
    total_annual = fields.Monetary(
        string="Total annuel global",
        readonly=True,
        currency_field='currency_id',
        compute='_compute_total_combined',
        store=True
    )

    # === RÉDUCTIONS ===
    reduction_children = fields.Integer(string="Réduction fratrie")
    reduction_children_applied = fields.Integer(string="% fratrie sollicité", default=0)
    reduction_seniority = fields.Integer(string="Réduction ancienneté")
    reduction_seniority_applied = fields.Integer(string="% ancienneté sollicité", default=0)
    total_reduction_percentage = fields.Float(
        string="Total réduction",
        compute="_compute_total_reduction",
        store=True
    )

    additional_reduction_request = fields.Selection([('yes','Oui'),('no','Non')], string="Demande réduction complémentaire")
    additional_reduction_income_percentage = fields.Float()
    additional_reduction_letter = fields.Text()
    annual_gross_income = fields.Float()
    proposed_monthly_amount = fields.Float()

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

    budget_line_ids = fields.One2many('ersge.budget.line','dossier_id')
    total_monthly_income = fields.Monetary(readonly=True, currency_field='currency_id')
    total_monthly_expenses = fields.Monetary(readonly=True, currency_field='currency_id')
    net_monthly_balance = fields.Monetary(readonly=True, currency_field='currency_id')
    budget_attachment = fields.Binary()
    budget_attachment_filename = fields.Char()

    tax_notice_attachment = fields.Binary()
    tax_notice_filename = fields.Char()
    tax_notice_status = fields.Selection([('draft','Brouillon'),('received','Reçu'),('validated','Validé')])
    tax_notice_date = fields.Date()

    payslip_parent1_ids = fields.Many2many('ir.attachment', relation='ersge_dossier_payslip_parent1_rel')
    payslip_parent1_status = fields.Selection([('draft','Brouillon'),('received','Reçu'),('validated','Validé')])
    payslip_parent2_ids = fields.Many2many('ir.attachment', relation='ersge_dossier_payslip_parent2_rel')
    payslip_parent2_status = fields.Selection([('draft','Brouillon'),('received','Reçu'),('validated','Validé')])
    attachment_ids = fields.Many2many('ir.attachment')

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
    # COMPUTE
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
        
    @api.depends('after_school_line_ids.montant_mensuel')
    def _compute_total_after_school(self):
        for record in self:
            record.total_monthly_after_school = sum(line.montant_mensuel for line in record.after_school_line_ids)
            record.total_annual_after_school = record.total_monthly_after_school * 12

    @api.depends('total_monthly_tuition','total_monthly_after_school')
    def _compute_total_combined(self):
        for record in self:
            record.total_monthly = (record.total_monthly_tuition or 0) + (record.total_monthly_after_school or 0)
            record.total_annual = (record.total_annual_tuition or 0) + (record.total_annual_after_school or 0)

    @api.depends('reduction_children_applied','reduction_seniority_applied')
    def _compute_total_reduction(self):
        for record in self:
            record.total_reduction_percentage = (record.reduction_children_applied or 0) + (record.reduction_seniority_applied or 0)

    @api.depends('legal_representation')
    def _compute_membership_fee_amount(self):
        for record in self:
            if record.legal_representation == 'both':
                record.membership_fee_amount = 60
            elif record.legal_representation == 'mother_only':
                record.membership_fee_amount = 40
            elif record.legal_representation == 'father_only':
                record.membership_fee_amount = 40
            elif record.legal_representation == 'other':
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
        return super().create(vals_list)

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