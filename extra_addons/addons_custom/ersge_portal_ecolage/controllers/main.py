# -*- coding: utf-8 -*-
import secrets
from datetime import datetime, timedelta
from odoo import http
from odoo.http import request
from odoo.exceptions import AccessError
import logging

_logger = logging.getLogger(__name__)


class PortalEcolage(http.Controller):

    # ==================== UTILITAIRES ====================
    def _get_partner_family(self, partner):
        return request.env['ersge.family'].sudo().search([
            ('parent_ids', 'in', [partner.id])
        ], limit=1)

    # ==================== CRÉATION DE FAMILLE AVEC CHOIX DU RÔLE ====================
    @http.route('/my/ecolage/family/create', type='http', auth='user', website=True, methods=['GET', 'POST'], csrf=False)
    def family_create(self, **kwargs):
        partner = request.env.user.partner_id
        # Si déjà membre d'une famille, rediriger vers la page des dossiers
        if partner.family_id:
            return request.redirect('/my/ecolage')

        if request.httprequest.method == 'POST':
            name = kwargs.get('name', '').strip()
            my_role = kwargs.get('my_role')
            if not name or not my_role or my_role not in ['parent1', 'parent2', 'tutor']:
                return request.render('ersge_portal_ecolage.portal_famille_create', {
                    'error': 'Tous les champs sont requis.',
                    'csrf_token': request.csrf_token()   # ← AJOUT
                })
            # Création de la famille
            family = request.env['ersge.family'].sudo().create({'name': name})
            # Mise à jour du partenaire connecté
            partner.sudo().write({
                'family_id': family.id,
                'family_role': my_role,
                'is_parent': True if my_role in ['parent1', 'parent2'] else False,
            })
            _logger.info(f"[family_create] Famille '{name}' créée par {partner.id} avec rôle {my_role}")
            # Rediriger vers la page d'invitation des autres membres
            return request.redirect('/my/ecolage/invite')

        # Affichage du formulaire (GET)
        return request.render('ersge_portal_ecolage.portal_famille_create', {
            'csrf_token': request.csrf_token()   # ← AJOUT
        })

    # ==================== INVITATIONS ====================
    @http.route('/my/ecolage/invite', type='http', auth='user', website=True, methods=['GET', 'POST'])
    def invite_partner(self, **kwargs):
        partner = request.env.user.partner_id
        if not partner.family_id:
            return request.redirect('/my/ecolage/family/create')
        family = partner.family_id

        if request.httprequest.method == 'POST':
            email = kwargs.get('email', '').strip()
            role = kwargs.get('role')
            if not email or role not in ['parent2', 'tutor']:
                return request.render('ersge_portal_ecolage.portal_invite_form', {
                    'error': 'Email et rôle valide requis',
                    'csrf_token': request.csrf_token()   # ← AJOUT
                })
            token = secrets.token_urlsafe(32)
            family.sudo().write({
                'invitation_token': token,
                'invitation_expiration': datetime.now() + timedelta(days=7),
                'invited_role': role
            })
            invite_link = request.httprequest.host_url + f'/my/ecolage/join?token={token}'
            _logger.info(f"[invite] Invitation envoyée à {email} pour le rôle {role} : {invite_link}")
            return request.render('ersge_portal_ecolage.portal_invite_sent', {'email': email})

        # GET : afficher le formulaire avec le token CSRF
        return request.render('ersge_portal_ecolage.portal_invite_form', {
            'csrf_token': request.csrf_token()   # ← AJOUT
        })
    @http.route('/my/ecolage/join', type='http', auth='public', website=True)
    def join_from_invite(self, token=None, **kwargs):
        if not token:
            return request.redirect('/')
        family = request.env['ersge.family'].sudo().search([('invitation_token', '=', token)], limit=1)
        if not family or (family.invitation_expiration and family.invitation_expiration < datetime.now()):
            return request.render('ersge_portal_ecolage.portal_invite_expired', {})
        # Si l'utilisateur n'est pas connecté, stocker le token en session et rediriger vers login
        if not request.session.uid:
            request.session['invitation_token'] = token
            return request.redirect('/web/login?redirect=/my/ecolage/join/confirm')
        # Utilisateur déjà connecté
        partner = request.env.user.partner_id
        partner.sudo().write({'family_id': family.id})
        if family.invited_role:
            partner.sudo().write({'family_role': family.invited_role})
        family.sudo().write({'invitation_token': False})
        return request.redirect('/my/ecolage')

    @http.route('/my/ecolage/join/confirm', type='http', auth='user', website=True)
    def join_confirm(self, **kwargs):
        token = request.session.get('invitation_token')
        if not token:
            return request.redirect('/my/ecolage')
        family = request.env['ersge.family'].sudo().search([('invitation_token', '=', token)], limit=1)
        if not family or (family.invitation_expiration and family.invitation_expiration < datetime.now()):
            return request.render('ersge_portal_ecolage.portal_invite_expired', {})
        partner = request.env.user.partner_id
        partner.sudo().write({'family_id': family.id})
        if family.invited_role:
            partner.sudo().write({'family_role': family.invited_role})
        family.sudo().write({'invitation_token': False})
        request.session.pop('invitation_token', None)
        return request.redirect('/my/ecolage')

    # ==================== DOSSIERS (routes existantes) ====================
    # Route de redirection pour les anciens liens /my/famille/new (optionnelle)
    @http.route('/my/famille/new', type='http', auth='user', website=True, methods=['GET', 'POST'])
    def famille_new(self, **kwargs):
        # Redirige simplement vers la nouvelle route de création de famille
        return request.redirect('/my/ecolage/family/create')

    @http.route('/my/ecolage/new', type='http', auth='user', website=True)
    def new_dossier(self, **kwargs):
        partner = request.env.user.partner_id
        if not partner.family_id:
            # Pas de famille, rediriger vers la création
            return request.redirect('/my/ecolage/family/create')
        try:
            new = request.env['ersge.dossier.famille'].sudo().with_context(
                default_family_id=partner.family_id.id
            ).create({
                'family_id': partner.family_id.id,
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

    @http.route('/my/ecolage', type='http', auth='user', website=True)
    def my_ecolage(self, **kwargs):
        partner = request.env.user.partner_id
        family = self._get_partner_family(partner)
        if family:
            dossiers = request.env['ersge.dossier.famille'].sudo().search([
                ('family_id', '=', family.id)
            ])
        else:
            # Fallback sur les dossiers où l'utilisateur est parent1 ou parent2
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

            # Vérification de l'accès via la famille
            if not partner.family_id or dossier.family_id.id != partner.family_id.id:
                raise AccessError("Vous n'avez pas accès à ce dossier.")

            if request.httprequest.method == 'POST':
                _logger.warning("=== POST RECU ===")
                _logger.warning(f"parent1_firstname = {request.params.get('parent1_firstname')}")
                _logger.warning(f"dossier.parent1_id avant = {dossier.parent1_id.id if dossier.parent1_id else None}")
                params = request.params.copy()
                params.pop('csrf_token', None)

                # Champs simples
                simple_fields = ['legal_representation', 'legal_representation_other', 'deposit_status',
                                'employer_assistance', 'send_invoice_to_employer', 'same_address_as_parent1',
                                'after_school_request', 'reduction_requested', 'requested_discount',
                                'gross_annual_income', 'additional_reduction_request', 'proposed_monthly_amount',
                                'contract_accepted', 'convention_accepted', 'procedures_accepted', 'terms_accepted',
                                'lpd_consent', 'explanatory_letter_text', 'explanatory_letter_mode']
                dossier_vals = {k: v for k, v in params.items() if k in simple_fields}
                if dossier_vals:
                    dossier.sudo().write(dossier_vals)

                # Parent 1
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
                fullname = f"{parent1_vals['firstname']} {parent1_vals['lastname']}".strip()
                parent1_vals['name'] = fullname if fullname else parent1_vals.get('email', 'Parent 1')

                if dossier.parent1_id:
                    dossier.parent1_id.sudo().write(parent1_vals)
                else:
                    new_parent1 = request.env['res.partner'].sudo().create(parent1_vals)
                    dossier.sudo().write({'parent1_id': new_parent1.id})

                # Parent 2
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
                    fullname2 = f"{parent2_vals['firstname']} {parent2_vals['lastname']}".strip()
                    parent2_vals['name'] = fullname2 if fullname2 else parent2_vals.get('email', 'Parent 2')
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
                        new_parent2 = request.env['res.partner'].sudo().create(parent2_vals)
                        dossier.sudo().write({'parent2_id': new_parent2.id})

                # Élèves (existants, suppressions, nouveaux)
                for key, value in params.items():
                    if key.startswith('student_line_id_'):
                        line_id = int(value)
                        line = request.env['ersge.dossier.student.line'].sudo().browse(line_id)
                        if line.exists() and line.dossier_id.id == dossier.id:
                            student_vals = {
                                'firstname': params.get(f'student_firstname_{line_id}', ''),
                                'lastname': params.get(f'student_lastname_{line_id}', ''),
                                'birthdate': params.get(f'student_birthdate_{line_id}') or False,
                                'gender': params.get(f'student_gender_{line_id}'),
                                'image_rights': params.get(f'student_image_rights_{line_id}') == '1',
                            }
                            line.student_id.sudo().write(student_vals)
                            forfait_key = f'forfait_id_{line_id}'
                            if forfait_key in params and params[forfait_key]:
                                line.sudo().write({'forfait_id': int(params[forfait_key])})
                            elif forfait_key in params:
                                line.sudo().write({'forfait_id': False})

                for key in list(params.keys()):
                    if key.startswith('delete_student_line_'):
                        line_id = int(key.replace('delete_student_line_', ''))
                        line = request.env['ersge.dossier.student.line'].sudo().browse(line_id)
                        if line.exists() and line.dossier_id.id == dossier.id:
                            line.unlink()

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

                # Employeur
                if params.get('employer_assistance') == 'yes' and params.get('send_invoice_to_employer') == '1':
                    employer_vals = {
                        'name': params.get('employer_name', ''),
                        'street': params.get('employer_street', ''),
                        'zip': params.get('employer_zip', ''),
                        'city': params.get('employer_city', ''),
                        'country_id': int(params['employer_country_id']) if params.get('employer_country_id') else False,
                        'is_employer': True,
                    }
                    if not employer_vals['name']:
                        employer_vals['name'] = 'Employeur'
                    existing = request.env['res.partner'].sudo().search([
                        ('name', '=', employer_vals['name']),
                        ('is_employer', '=', True)
                    ], limit=1)
                    employer = existing if existing else request.env['res.partner'].sudo().create(employer_vals)
                    dossier.sudo().write({'employer_id': employer.id})
                else:
                    dossier.sudo().write({'employer_id': False})

                return request.redirect('/my/ecolage?success=1')

            # GET: afficher le formulaire
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