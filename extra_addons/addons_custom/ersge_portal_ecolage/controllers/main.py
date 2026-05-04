# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.exceptions import AccessError
import logging

_logger = logging.getLogger(__name__)

class PortalEcolage(http.Controller):

    def _get_partner_family(self, partner):
        return request.env['ersge.family'].sudo().search([
            ('parent_ids', 'in', [partner.id])
        ], limit=1)

    @http.route('/my/famille/new', type='http', auth='user', website=True, methods=['GET', 'POST'])
    def famille_new(self, **kwargs):
        partner = request.env.user.partner_id
        next_url = kwargs.get('next', '/my/ecolage/new')

        # Si l'utilisateur a déjà une famille, rediriger directement
        family = self._get_partner_family(partner)
        if family:
            return request.redirect(next_url)

        # Traitement POST
        if request.httprequest.method == 'POST':
            nom = kwargs.get('nom', '').strip()

            if not nom:
                return request.render('ersge_portal_ecolage.portal_famille_new', {
                    'partner': partner,
                    'next': next_url,
                    'error': 'Le nom de famille est obligatoire.',
                })

            try:
                family = request.env['ersge.family'].sudo().create({
                    'name': nom,
                })
                partner.sudo().write({
                    'family_id': family.id,
                    'is_parent': True,
                })
                _logger.info(f"[famille_new] Famille '{nom}' créée id={family.id} pour partner={partner.id}")
                return request.redirect(next_url)

            except Exception as e:
                _logger.exception(f"[famille_new] ERREUR: {e}")
                return request.render('ersge_portal_ecolage.portal_famille_new', {
                    'partner': partner,
                    'next': next_url,
                    'error': f"Une erreur est survenue : {str(e)}",
                })

        # Affichage GET
        return request.render('ersge_portal_ecolage.portal_famille_new', {
            'partner': partner,
            'next': next_url,
            'error': kwargs.get('error'),
        })

    # ─── ROUTE EXISTANTE : modifiée pour rediriger au lieu d'afficher erreur ──
    @http.route('/my/ecolage/new', type='http', auth='user', website=True)
    def new_dossier(self, **kwargs):
        try:
            partner = request.env.user.partner_id
            family = self._get_partner_family(partner)

            if not family:
                # ← Redirection vers création famille au lieu du message d'erreur
                return request.redirect('/my/famille/new?next=/my/ecolage/new')

            new = request.env['ersge.dossier.famille'].sudo().with_context(
                default_family_id=family.id
            ).create({
                'family_id': family.id,
                'annee_scolaire': request.env['ersge.dossier.famille']._get_current_school_year(),
                'state': 'incomplet',
            })
            return request.redirect(f'/my/ecolage/edit/{new.id}')

        except Exception as e:
            _logger.exception(f"[new_dossier] ERREUR: {e}")
            return request.render('ersge_portal_ecolage.portal_my_dossiers', {
                'dossiers': [],
                'error': f"Une erreur est survenue : {str(e)}",
            })

    # ─── ROUTES EXISTANTES INCHANGÉES ─────────────────────────────────────────
    @http.route('/my/ecolage', type='http', auth='user', website=True)
    def my_ecolage(self, **kwargs):
        partner = request.env.user.partner_id
        family = self._get_partner_family(partner)
        if family:
            dossiers = request.env['ersge.dossier.famille'].sudo().search([
                ('family_id', '=', family.id)
            ])
        else:
            # Fallback : recherche sur parent1/parent2 (ancienne méthode)
            dossiers = request.env['ersge.dossier.famille'].sudo().search([
                '|',
                ('parent1_id', '=', partner.id),
                ('parent2_id', '=', partner.id),
            ])
        return request.render('ersge_portal_ecolage.portal_my_dossiers', {
            'dossiers': dossiers,
            'error': kwargs.get('error'),
        })

    @http.route('/my/ecolage/edit/<int:dossier_id>', type='http', auth='user', website=True, methods=['GET', 'POST'])
    def edit_dossier(self, dossier_id, **kwargs):
        try:
            partner = request.env.user.partner_id
            dossier = request.env['ersge.dossier.famille'].sudo().browse(dossier_id)
            if not dossier.exists():
                return request.redirect('/my/ecolage')

            family = self._get_partner_family(partner)
            is_parent = (
                dossier.parent1_id.id == partner.id or
                dossier.parent2_id.id == partner.id
            )
            is_family_member = family and dossier.family_id.id == family.id

            if not (is_parent or is_family_member):
                raise AccessError("Vous n'avez pas accès à ce dossier.")

            # ================== TRAITEMENT POST ==================
            if request.httprequest.method == 'POST':
                params = request.params.copy()
                params.pop('csrf_token', None)

                # 1. Mise à jour des champs simples du dossier (qui existent directement)
                simple_fields = ['legal_representation', 'legal_representation_other', 'deposit_status',
                                'employer_assistance', 'send_invoice_to_employer', 'same_address_as_parent1',
                                'after_school_request', 'reduction_requested', 'requested_discount',
                                'gross_annual_income', 'additional_reduction_request', 'proposed_monthly_amount',
                                'contract_accepted', 'convention_accepted', 'procedures_accepted', 'terms_accepted',
                                'lpd_consent', 'explanatory_letter_text', 'explanatory_letter_mode']
                dossier_vals = {k: v for k, v in params.items() if k in simple_fields}
                if dossier_vals:
                    dossier.sudo().write(dossier_vals)

                # 2. Gestion du Parent 1 (création ou mise à jour)
                parent1_vals = {
                    'firstname': params.get('parent1_firstname', ''),
                    'lastname': params.get('parent1_lastname', ''),
                    'email': params.get('parent1_email', ''),
                    'phone': params.get('parent1_phone', ''),
                    'phone_fixed': params.get('parent1_phone_fixed', ''),
                    'phone_pro': params.get('parent1_phone_pro', ''),
                    'street': params.get('parent1_street', ''),
                    'zip': params.get('parent1_zip', ''),
                    'city': params.get('parent1_city', ''),
                    'profession': params.get('parent1_profession', ''),
                    'employer_name': params.get('parent1_employeur', ''),
                    'is_parent': True,
                    'family_id': dossier.family_id.id,
                }
                if dossier.parent1_id:
                    dossier.parent1_id.sudo().write(parent1_vals)
                else:
                    # Créer un nouveau partenaire
                    parent1 = request.env['res.partner'].sudo().create(parent1_vals)
                    dossier.sudo().write({'parent1_id': parent1.id})

                # 3. Gestion du Parent 2
                if params.get('parent2_firstname') or params.get('parent2_lastname'):
                    parent2_vals = {
                        'firstname': params.get('parent2_firstname', ''),
                        'lastname': params.get('parent2_lastname', ''),
                        'email': params.get('parent2_email', ''),
                        'phone': params.get('parent2_phone', ''),
                        'phone_fixed': params.get('parent2_phone_fixed', ''),
                        'phone_pro': params.get('parent2_phone_pro', ''),
                        'profession': params.get('parent2_profession', ''),
                        'employer_name': params.get('parent2_employeur', ''),
                        'is_parent': True,
                        'family_id': dossier.family_id.id,
                    }
                    same_addr = params.get('same_address_as_parent1') == '1'
                    if same_addr and dossier.parent1_id:
                        parent2_vals.update({
                            'street': dossier.parent1_id.street,
                            'zip': dossier.parent1_id.zip,
                            'city': dossier.parent1_id.city,
                            'country_id': dossier.parent1_id.country_id.id,
                        })
                    else:
                        parent2_vals.update({
                            'street': params.get('parent2_street', ''),
                            'zip': params.get('parent2_zip', ''),
                            'city': params.get('parent2_city', ''),
                        })
                    if dossier.parent2_id:
                        dossier.parent2_id.sudo().write(parent2_vals)
                    else:
                        parent2 = request.env['res.partner'].sudo().create(parent2_vals)
                        dossier.sudo().write({'parent2_id': parent2.id})

                # 4. Gestion des lignes élèves existantes (modification)
                for key, value in params.items():
                    if key.startswith('student_line_id_'):
                        line_id = int(value)
                        line = request.env['ersge.dossier.student.line'].sudo().browse(line_id)
                        if line.exists() and line.dossier_id.id == dossier.id:
                            # Mise à jour des données de l'élève (student_id)
                            student_vals = {
                                'firstname': params.get(f'student_firstname_{line_id}', ''),
                                'lastname': params.get(f'student_lastname_{line_id}', ''),
                                'birthdate': params.get(f'student_birthdate_{line_id}') or False,
                                'gender': params.get(f'student_gender_{line_id}'),
                                'image_rights': params.get(f'student_image_rights_{line_id}') == '1',
                            }
                            line.student_id.sudo().write(student_vals)
                            # Mise à jour du forfait sur la ligne
                            forfait_key = f'forfait_id_{line_id}'
                            if forfait_key in params and params[forfait_key]:
                                line.sudo().write({'forfait_id': int(params[forfait_key])})
                            elif forfait_key in params:
                                line.sudo().write({'forfait_id': False})

                # 5. Suppression d'élèves
                for key in list(params.keys()):
                    if key.startswith('delete_student_line_'):
                        line_id = int(key.replace('delete_student_line_', ''))
                        line = request.env['ersge.dossier.student.line'].sudo().browse(line_id)
                        if line.exists() and line.dossier_id.id == dossier.id:
                            line.unlink()

                # 6. Ajout de nouveaux élèves
                new_firstnames = params.getlist('new_student_firstname[]')
                new_lastnames = params.getlist('new_student_lastname[]')
                new_birthdates = params.getlist('new_student_birthdate[]')
                new_genders = params.getlist('new_student_gender[]')
                new_image_rights = params.getlist('new_student_image_rights[]')
                for i in range(len(new_firstnames)):
                    if new_firstnames[i] or new_lastnames[i]:
                        student = request.env['ersge.student'].sudo().create({
                            'firstname': new_firstnames[i],
                            'lastname': new_lastnames[i],
                            'birthdate': new_birthdates[i] or False,
                            'gender': new_genders[i],
                            'image_rights': new_image_rights[i] == '1',
                            'family_id': dossier.family_id.id,
                        })
                        request.env['ersge.dossier.student.line'].sudo().create({
                            'dossier_id': dossier.id,
                            'student_id': student.id,
                        })

                # 7. Gestion de l'employeur
                if params.get('employer_assistance') == 'yes' and params.get('send_invoice_to_employer') == '1':
                    employer_vals = {
                        'name': params.get('employer_name', ''),
                        'street': params.get('employer_street', ''),
                        'zip': params.get('employer_zip', ''),
                        'city': params.get('employer_city', ''),
                        'country_id': int(params['employer_country_id']) if params.get('employer_country_id') else False,
                        'is_employer': True,
                    }
                    # Vérifier si un employeur avec ce nom existe déjà
                    existing = request.env['res.partner'].sudo().search([
                        ('name', '=', employer_vals['name']),
                        ('is_employer', '=', True)
                    ], limit=1)
                    employer = existing if existing else request.env['res.partner'].sudo().create(employer_vals)
                    dossier.sudo().write({'employer_id': employer.id})
                else:
                    dossier.sudo().write({'employer_id': False})

                # Redirection après sauvegarde
                return request.redirect('/my/ecolage?success=1')

            # ================== AFFICHAGE GET ==================
            countries = request.env['res.country'].sudo().search([])
            forfaits = request.env['ersge.forfait'].sudo().search([('active', '=', True)])
            return request.render('ersge_portal_ecolage.portal_dossier_form_complete', {
                'dossier': dossier,
                'csrf_token': request.csrf_token(),
                'countries': countries,
                'forfaits': forfaits,
            })

        except AccessError:
            raise
        except Exception as e:
            _logger.exception(f"[edit_dossier] ERREUR: {e}")
            return request.redirect('/my/ecolage')