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
        if partner.family_id:
            return request.redirect('/my/ecolage')

        if request.httprequest.method == 'POST':
            name = kwargs.get('name', '').strip()
            my_role = kwargs.get('my_role')
            if not name or not my_role or my_role not in ['parent1', 'parent2', 'tutor']:
                return request.render('ersge_portal_ecolage.portal_famille_create', {
                    'error': 'Tous les champs sont requis.',
                    'csrf_token': request.csrf_token()
                })

            # Création famille
            family = request.env['ersge.family'].sudo().create({'name': name})
            partner.sudo().write({
                'family_id': family.id,
                'family_role': my_role,
                'is_parent': my_role in ['parent1', 'parent2'],
            })

            # ✅ Création immédiate du dossier
            new_dossier = request.env['ersge.dossier.famille'].sudo().with_context(
                default_family_id=family.id
            ).create({
                'family_id': family.id,
                'annee_scolaire': request.env['ersge.dossier.famille']._get_current_school_year(),
                'state': 'incomplet',
            })

            # ✅ Si parent1 ou parent2 : proposer l'invitation (page intermédiaire)
            # Si tuteur : aller directement au dossier
            if my_role in ['parent1', 'parent2']:
                return request.redirect(f'/my/ecolage/invite?dossier_id={new_dossier.id}')
            else:
                return request.redirect(f'/my/ecolage/edit/{new_dossier.id}')

        return request.render('ersge_portal_ecolage.portal_famille_create', {
            'csrf_token': request.csrf_token()
        })

    # ==================== INVITATIONS ====================
    @http.route('/my/ecolage/invite', type='http', auth='user', website=True, methods=['GET', 'POST'])
    def invite_partner(self, **kwargs):
        partner = request.env.user.partner_id
        if not partner.family_id:
            return request.redirect('/my/ecolage/family/create')

        # ✅ Tuteur : pas d'accès à cette page
        if partner.family_role == 'tutor':
            return request.redirect('/my/ecolage')

        family = partner.family_id
        dossier_id = kwargs.get('dossier_id')  # passé en query string depuis family_create

        if request.httprequest.method == 'POST':
            email = kwargs.get('email', '').strip()
            role = kwargs.get('role')
            dossier_id = kwargs.get('dossier_id')

            # ✅ Bouton "Passer cette étape" : soumis sans email
            if not email:
                if dossier_id:
                    return request.redirect(f'/my/ecolage/edit/{dossier_id}')
                return request.redirect('/my/ecolage')

            if role not in ['parent2', 'tutor']:
                return request.render('ersge_portal_ecolage.portal_invite_form', {
                    'error': 'Rôle invalide.',
                    'dossier_id': dossier_id,
                    'csrf_token': request.csrf_token()
                })

            # Générer et stocker le token
            token = secrets.token_urlsafe(32)
            family.sudo().write({
                'invitation_token': token,
                'invitation_expiration': datetime.now() + timedelta(days=7),
                'invited_role': role,
            })

            # Envoyer l'email
            invite_link = request.httprequest.host_url.rstrip('/') + f'/my/ecolage/join?token={token}'
            try:
                request.env['mail.mail'].sudo().create({
                    'subject': f"Invitation à rejoindre la famille {family.name}",
                    'email_to': email,
                    'body_html': f"""
                        <p>Bonjour,</p>
                        <p>Vous avez été invité(e) à rejoindre la famille <strong>{family.name}</strong>
                        en tant que <strong>{role}</strong>.</p>
                        <p><a href="{invite_link}">Cliquez ici pour accepter l'invitation</a></p>
                        <p>Ce lien expire dans 7 jours.</p>
                    """,
                    'auto_delete': True,
                }).send()
            except Exception as e:
                _logger.exception(f"[invite] Erreur envoi email : {e}")

            # ✅ Rediriger vers le dossier après envoi
            if dossier_id:
                return request.redirect(f'/my/ecolage/edit/{dossier_id}')
            return request.redirect('/my/ecolage')

        # GET
        return request.render('ersge_portal_ecolage.portal_invite_form', {
            'dossier_id': dossier_id,
            'csrf_token': request.csrf_token()
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

            if not partner.family_id or dossier.family_id.id != partner.family_id.id:
                raise AccessError("Vous n'avez pas accès à ce dossier.")

            if request.httprequest.method == 'POST':
                params = request.params
                form = request.httprequest.form

                _logger.warning("========== DEBUT POST DOSSIER %s ==========", dossier.id)

                # ========== 1. CRÉATION DES NOUVEAUX ÉLÈVES (avant réduction) ==========
                new_firstnames = form.getlist('new_student_firstname[]')
                new_lastnames = form.getlist('new_student_lastname[]')
                new_birthdates = form.getlist('new_student_birthdate[]')
                new_genders = form.getlist('new_student_gender[]')
                raw_image_rights = form.getlist('new_student_image_rights[]')

                for i in range(len(new_firstnames)):
                    if new_firstnames[i] or new_lastnames[i]:
                        vals_ir = raw_image_rights[2*i+1] == '1' if (2*i+1) < len(raw_image_rights) else False
                        student = request.env['ersge.student'].sudo().create({
                            'firstname': new_firstnames[i],
                            'lastname': new_lastnames[i],
                            'birthdate': new_birthdates[i] or False,
                            'gender': new_genders[i],
                            'image_rights': vals_ir,
                            'family_id': dossier.family_id.id,
                        })
                        request.env['ersge.dossier.student.line'].sudo().create({
                            'dossier_id': dossier.id,
                            'student_id': student.id,
                        })
                        _logger.warning("Nouvel élève créé: %s %s", new_firstnames[i], new_lastnames[i])
                # ========== 2. MISE À JOUR DES ÉLÈVES EXISTANTS (prénoms, noms, forfaits, droit à l'image) ==========
                for key in list(params.keys()):
                    if key.startswith('student_line_id_'):
                        line_id = int(params.get(key))
                        line = request.env['ersge.dossier.student.line'].sudo().browse(line_id)
                        if line.exists() and line.dossier_id.id == dossier.id:
                            # ---- Droit à l'image : checkbox + hidden ----
                            checkbox_key = f'student_image_rights_{line_id}'
                            hidden_key = f'student_image_rights_hidden_{line_id}'
                            if checkbox_key in params:
                                image_rights = params.get(checkbox_key) == '1'
                            else:
                                image_rights = params.get(hidden_key, '0') == '1'

                            student_vals = {
                                'firstname': params.get(f'student_firstname_{line_id}', ''),
                                'lastname': params.get(f'student_lastname_{line_id}', ''),
                                'birthdate': params.get(f'student_birthdate_{line_id}') or False,
                                'gender': params.get(f'student_gender_{line_id}'),
                                'image_rights': image_rights,
                            }
                            _logger.warning(f"Élève {line_id} : checkbox présent = {checkbox_key in params}, hidden présent = {hidden_key in params} -> image_rights = {image_rights}")
                            line.student_id.sudo().write(student_vals)

                            # Forfait
                            forfait_key = f'forfait_id_{line_id}'
                            if forfait_key in params:
                                forfait_val = params.get(forfait_key)
                                line.sudo().write({'forfait_id': int(forfait_val) if forfait_val else False})
                                _logger.warning("Forfait ligne %s: %s", line_id, forfait_val)

                # ========== 3. ÉCRITURE DES CHAMPS SIMPLES DU DOSSIER (dont réductions) ==========
                simple_fields = [
                    'legal_representation', 'legal_representation_other', 'deposit_status',
                    'employer_assistance', 'send_invoice_to_employer', 'same_address_as_parent1',
                    'after_school_request', 'reduction_requested', 'requested_discount',
                    'gross_annual_income', 'additional_reduction_request', 'proposed_monthly_amount',
                    'contract_accepted', 'convention_accepted', 'procedures_accepted', 'terms_accepted',
                    'lpd_consent', 'explanatory_letter_text', 'explanatory_letter_mode',
                    'budget_method',
                    'apply_children_discount', 'apply_seniority_discount', 'seniority_years',
                ]
                dossier_vals = {}
                for k in simple_fields:
                    if k in params:
                        val = params.get(k)
                        if k in ('send_invoice_to_employer', 'same_address_as_parent1', 'reduction_requested',
                                'additional_reduction_request', 'contract_accepted', 'convention_accepted',
                                'procedures_accepted', 'terms_accepted', 'lpd_consent',
                                'apply_children_discount', 'apply_seniority_discount'):
                            dossier_vals[k] = val == '1'
                        else:
                            dossier_vals[k] = val

                # Nouveaux champs sections 7-9
                if params.get('solidarity_request') in ('yes', 'no'):
                    dossier_vals['solidarity_request'] = params.get('solidarity_request')
                if params.get('sponsorship_request') in ('yes', 'no'):
                    dossier_vals['sponsorship_request'] = params.get('sponsorship_request')
                if params.get('payment_terms') in ('monthly', 'annually'):
                    dossier_vals['payment_terms'] = params.get('payment_terms')
                bool_fields = ['apply_solidarity_increase', 'address_book_optin', 'multi_billing_request']
                for field in bool_fields:
                    if field in params:
                        dossier_vals[field] = params.get(field) == '1'
                if params.get('solidarity_percentage'):
                    try:
                        dossier_vals['solidarity_percentage'] = float(params.get('solidarity_percentage'))
                    except ValueError:
                        pass
                if 'comments' in params:
                    dossier_vals['comments'] = params.get('comments')
                if 'signature_text' in params:
                    dossier_vals['signature_text'] = params.get('signature_text')

                if dossier_vals:
                    _logger.warning("Écriture dossier_vals: %s", dossier_vals)
                    dossier.sudo().write(dossier_vals)

                # ========== 4. FICHIER BUDGET ==========
                budget_attachment = request.httprequest.files.get('budget_attachment')
                if budget_attachment and budget_attachment.filename:
                    attachment = request.env['ir.attachment'].sudo().create({
                        'name': budget_attachment.filename,
                        'datas': budget_attachment.read().hex(),
                        'res_model': 'ersge.dossier.famille',
                        'res_id': dossier.id,
                        'mimetype': budget_attachment.content_type or 'application/pdf',
                    })
                    dossier.sudo().write({'budget_attachment': attachment.id})

                # ========== 5. PARENT 1 ==========
                parent1_vals = {
                    'firstname': params.get('parent1_firstname', '').strip(),
                    'lastname': params.get('parent1_lastname', '').strip(),
                    'email': params.get('parent1_email', '').strip(),
                    'phone': params.get('parent1_phone', '').strip(),
                    'phone_fixed': params.get('parent1_phone_fixed', '').strip(),
                    'phone_pro': params.get('parent1_phone_pro', '').strip(),
                    'street': params.get('parent1_street', '').strip(),
                    'zip': params.get('parent1_zip', '').strip(),
                    'city': params.get('parent1_city', '').strip(),
                    'profession': params.get('parent1_profession', '').strip(),
                    'employer_name': params.get('parent1_employeur', '').strip(),
                    'is_parent': True,
                    'family_id': dossier.family_id.id,
                    'family_role': 'parent1',
                }
                fullname = f"{parent1_vals['firstname']} {parent1_vals['lastname']}".strip()
                parent1_vals['name'] = fullname if fullname else parent1_vals.get('email', 'Parent 1')
                if 'parent1_country_id' in params and params.get('parent1_country_id'):
                    parent1_vals['country_id'] = int(params.get('parent1_country_id'))

                if dossier.parent1_id:
                    dossier.parent1_id.sudo().write(parent1_vals)
                else:
                    if partner.family_role == 'parent1' and partner.family_id.id == dossier.family_id.id:
                        partner.sudo().write(parent1_vals)
                        dossier.sudo().write({'parent1_id': partner.id})
                    else:
                        existing = request.env['res.partner'].sudo().search([
                            ('firstname', '=', parent1_vals['firstname']),
                            ('lastname', '=', parent1_vals['lastname']),
                            ('family_id', '=', dossier.family_id.id),
                        ], limit=1)
                        if existing:
                            existing.sudo().write(parent1_vals)
                            dossier.sudo().write({'parent1_id': existing.id})
                        else:
                            new_parent1 = request.env['res.partner'].sudo().create(parent1_vals)
                            dossier.sudo().write({'parent1_id': new_parent1.id})

                # ========== 6. PARENT 2 ==========
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
                            'street': dossier.parent1_id.street or '',
                            'zip': dossier.parent1_id.zip or '',
                            'city': dossier.parent1_id.city or '',
                            'country_id': dossier.parent1_id.country_id.id if dossier.parent1_id.country_id else False,
                        })
                    else:
                        parent2_vals.update({
                            'street': params.get('parent2_street', ''),
                            'zip': params.get('parent2_zip', ''),
                            'city': params.get('parent2_city', ''),
                        })
                    if 'parent2_country_id' in params and params.get('parent2_country_id'):
                        parent2_vals['country_id'] = int(params.get('parent2_country_id'))

                    if dossier.parent2_id:
                        dossier.parent2_id.sudo().write(parent2_vals)
                    else:
                        new_parent2 = request.env['res.partner'].sudo().create(parent2_vals)
                        dossier.sudo().write({'parent2_id': new_parent2.id})

                # ========== 7. AUTRE REPRÉSENTANT LÉGAL ==========
                other_fields = [
                    'other_firstname', 'other_lastname', 'other_email',
                    'other_phone', 'other_phone_fixed', 'other_phone_pro',
                    'other_street', 'other_zip', 'other_city',
                    'other_profession', 'other_employeur', 'other_country_id'
                ]
                other_vals = {}
                for field in other_fields:
                    if field in params:
                        val = params.get(field)
                        if field == 'other_country_id':
                            other_vals[field] = int(val) if val else False
                        else:
                            other_vals[field] = val.strip() if isinstance(val, str) else val
                if other_vals:
                    dossier.sudo().write(other_vals)

                # ========== 8. BUDGET EN LIGNE ==========
                if params.get('budget_method') == 'online':
                    for key, value in params.items():
                        if key.startswith('montant_madame_'):
                            line_id = int(key.split('_')[-1])
                            monsieur_key = f'montant_monsieur_{line_id}'
                            montant_madame = float(value or 0)
                            montant_monsieur = float(params.get(monsieur_key, 0) or 0)
                            line = request.env['ersge.budget.line'].sudo().browse(line_id)
                            if line.exists() and line.dossier_id.id == dossier.id:
                                line.sudo().write({
                                    'montant_madame': montant_madame,
                                    'montant_monsieur': montant_monsieur,
                                })
                    _logger.warning("Budget en ligne sauvegardé")

                # ========== 9. EMPLOYEUR ==========
                if params.get('employer_assistance') == 'yes' and params.get('send_invoice_to_employer') == '1':
                    employer_vals = {
                        'name': params.get('employer_name', ''),
                        'street': params.get('employer_street', ''),
                        'zip': params.get('employer_zip', ''),
                        'city': params.get('employer_city', ''),
                        'country_id': int(params.get('employer_country_id')) if params.get('employer_country_id') else False,
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

                # ========== 10. PARASCOLAIRE ==========
                _logger.warning("========== SAUVEGARDE PARASCOLAIRE ==========")
                existing_after_lines = dossier.after_school_line_ids
                _logger.warning("Lignes parascolaires existantes : %s", existing_after_lines.ids)

                for student_line in dossier.student_line_ids:
                    selected_key = f'after_school_selected_{student_line.id}'
                    selected = params.get(selected_key) == '1'
                    _logger.warning("Élève line %s (student_id=%s) - selected_key=%s - selected=%s",
                                    student_line.id, student_line.student_id.id, selected_key, selected)

                    after_line = existing_after_lines.filtered(lambda l: l.student_id.id == student_line.student_id.id)
                    if selected:
                        accueil_type = params.get(f'accueil_type_{student_line.id}')
                        _logger.warning("   accueil_type = %s", accueil_type)

                        prestation_ids = []
                        prestations = request.env['ersge.after.school.prestation'].sudo().search([])
                        for prestation in prestations:
                            prestation_key = f'prestation_{student_line.id}_{prestation.id}'
                            if params.get(prestation_key) == '1':
                                prestation_ids.append(prestation.id)
                        _logger.warning("   prestations sélectionnées (ids) : %s", prestation_ids)

                        if after_line:
                            after_line.sudo().write({
                                'selected': True,
                                'accueil_type': accueil_type,
                                'prestation_ids': [(6, 0, prestation_ids)],
                            })
                            _logger.warning("   Mise à jour ligne existante %s", after_line.id)
                        else:
                            new_line = request.env['ersge.after.school.line'].sudo().create({
                                'dossier_id': dossier.id,
                                'student_id': student_line.student_id.id,
                                'selected': True,
                                'accueil_type': accueil_type,
                                'prestation_ids': [(6, 0, prestation_ids)],
                            })
                            _logger.warning("   Création nouvelle ligne %s", new_line.id)
                    else:
                        if after_line:
                            after_line.sudo().unlink()
                            _logger.warning("   Suppression ligne %s", after_line.id)

                _logger.warning("========== FIN POST ==========")
                if params.get('redirect_to_edit'):
                    return request.redirect(f'/my/ecolage/edit/{dossier.id}')
                return request.redirect('/my/ecolage?success=1')

            # ==================== GET ====================
            prefill_firstname = partner.firstname or ''
            prefill_lastname = partner.lastname or partner.name or ''

            prefill_parent1 = {}
            if not dossier.parent1_id and partner.family_role in ['parent1', 'parent2']:
                prefill_parent1 = {
                    'firstname': prefill_firstname,
                    'lastname': prefill_lastname,
                    'email': partner.email or '',
                    'phone': partner.phone or '',
                    'phone_fixed': getattr(partner, 'phone_fixed', '') or '',
                    'phone_pro': getattr(partner, 'phone_pro', '') or '',
                    'street': partner.street or '',
                    'zip': partner.zip or '',
                    'city': partner.city or '',
                }

            prefill_parent2 = {}
            if not dossier.parent2_id and partner.family_role == 'parent2':
                prefill_parent2 = {
                    'firstname': prefill_firstname,
                    'lastname': prefill_lastname,
                    'email': partner.email or '',
                    'phone': partner.phone or '',
                    'phone_fixed': getattr(partner, 'phone_fixed', '') or '',
                    'phone_pro': getattr(partner, 'phone_pro', '') or '',
                    'street': partner.street or '',
                    'zip': partner.zip or '',
                    'city': partner.city or '',
                }

            prefill_tutor = {}
            if not dossier.parent1_id and partner.family_role == 'tutor':
                prefill_tutor = {
                    'firstname': prefill_firstname,
                    'lastname': prefill_lastname,
                    'email': partner.email or '',
                    'phone': partner.phone or '',
                    'phone_fixed': getattr(partner, 'phone_fixed', '') or '',
                    'phone_pro': getattr(partner, 'phone_pro', '') or '',
                    'street': partner.street or '',
                    'zip': partner.zip or '',
                    'city': partner.city or '',
                }

            countries = request.env['res.country'].sudo().search([])
            forfaits = request.env['ersge.forfait'].sudo().search([('active', '=', True)])
            after_school_prestations = request.env['ersge.after.school.prestation'].sudo().search([('active', '=', True)])

            return request.render('ersge_portal_ecolage.portal_dossier_form_complete', {
                'dossier': dossier,
                'prefill_parent1': prefill_parent1,
                'prefill_parent2': prefill_parent2,
                'prefill_tutor': prefill_tutor,
                'csrf_token': request.csrf_token(),
                'countries': countries,
                'forfaits': forfaits,
                'after_school_prestations': after_school_prestations,
            })

        except AccessError:
            raise
        except Exception as e:
            _logger.exception(f"[edit_dossier] ERREUR: {e}")
            return request.redirect('/my/ecolage')



    @http.route('/my/ecolage/delete_student_line', type='json', auth='user', methods=['POST'], csrf=True)
    def delete_student_line(self):
        data = request.get_json_data()
        line_id = data.get('line_id')
        if not line_id:
            return {'success': False, 'error': 'ID manquant'}
        try:
            line = request.env['ersge.dossier.student.line'].sudo().browse(int(line_id))
            if not line.exists():
                return {'success': False, 'error': 'Ligne introuvable'}
            partner = request.env.user.partner_id
            dossier = line.dossier_id
            if partner.family_id and dossier.family_id.id == partner.family_id.id:
                # AVANT suppression, mettre requested_discount à 0 pour éviter la validation
                dossier.sudo().write({'requested_discount': 0.0})
                line.unlink()
                return {'success': True}
            else:
                return {'success': False, 'error': 'Accès non autorisé'}
        except Exception as e:
            return {'success': False, 'error': str(e)}