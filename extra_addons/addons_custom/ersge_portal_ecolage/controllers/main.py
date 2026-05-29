# -*- coding: utf-8 -*-
import secrets
from datetime import datetime, timedelta
from odoo import http
from odoo.http import request
from odoo import fields
from odoo.exceptions import AccessError
import logging

_logger = logging.getLogger(__name__)


class PortalEcolage(http.Controller):

    # ==================== UTILITAIRES ====================

    def _get_partner_family(self, partner):
        """Retourne la famille du partner (ancienne logique, gardée en fallback)."""
        return request.env['ersge.family'].sudo().search([
            ('parent_ids', 'in', [partner.id])
        ], limit=1)

    def _check_dossier_access(self, dossier, partner):
        """
        Vérifie si le partner a accès au dossier.
        Priorité : nouvelle table ersge.dossier.acces
        Fallback  : ancienne logique family_id (migration progressive)
        """
        # Nouvelle logique
        acces = request.env['ersge.dossier.acces'].sudo().search([
            ('dossier_id', '=', dossier.id),
            ('partner_id', '=', partner.id),
            ('invite_state', '=', 'accepted'),
        ], limit=1)
        if acces:
            return True

        # Fallback ancienne logique (pendant la migration)
        if partner.family_id and dossier.family_id.id == partner.family_id.id:
            return True

        return False

    def _get_partner_dossiers(self, partner):
        """
        Retourne tous les dossiers accessibles par le partner.
        Combine nouvelle logique + ancienne logique.
        """
        # Nouvelle logique : via ersge.dossier.acces
        acces_records = request.env['ersge.dossier.acces'].sudo().search([
            ('partner_id', '=', partner.id),
            ('invite_state', '=', 'accepted'),
        ])
        dossiers_via_acces = acces_records.mapped('dossier_id')

        # Ancienne logique : via family_id (fallback migration)
        family = self._get_partner_family(partner)
        if family:
            dossiers_via_family = request.env['ersge.dossier.famille'].sudo().search([
                ('family_id', '=', family.id)
            ])
        else:
            dossiers_via_family = request.env['ersge.dossier.famille'].sudo().search([
                '|',
                ('parent1_id', '=', partner.id),
                ('parent2_id', '=', partner.id),
            ])

        # Union des deux sans doublon
        all_dossiers = dossiers_via_acces | dossiers_via_family
        return all_dossiers

    # ==================== LISTE DES DOSSIERS ====================

    @http.route('/my/ecolage', type='http', auth='user', website=True)
    def my_ecolage(self, **kwargs):
        partner = request.env.user.partner_id
        dossiers = self._get_partner_dossiers(partner)

        return request.render('ersge_portal_ecolage.portal_my_dossiers', {
            'dossiers':   dossiers,
            'error':      kwargs.get('error'),
            'success':    kwargs.get('success'),
            'csrf_token': request.csrf_token(),
        })

    # ==================== CRÉATION DE FAMILLE ====================

    @http.route(
        '/my/ecolage/family/create',
        type='http', auth='user', website=True,
        methods=['GET', 'POST'], csrf=False,
    )
    def family_create(self, **kwargs):
        partner = request.env.user.partner_id
        if partner.family_id:
            return request.redirect('/my/ecolage')

        if request.httprequest.method == 'POST':
            name    = kwargs.get('name', '').strip()
            my_role = kwargs.get('my_role')

            if not name or my_role not in ['parent1', 'parent2', 'tutor']:
                return request.render(
                    'ersge_portal_ecolage.portal_famille_create',
                    {
                        'error':      'Tous les champs sont requis.',
                        'csrf_token': request.csrf_token(),
                    },
                )

            # Création famille
            family = request.env['ersge.family'].sudo().create(
                {'name': name}
            )
            partner.sudo().write({
                'family_id':   family.id,
                'family_role': my_role,
                'is_parent':   my_role in ['parent1', 'parent2'],
            })

            # Création du dossier
            new_dossier = request.env['ersge.dossier.famille'].sudo()\
                .with_context(default_family_id=family.id).create({
                    'family_id':      family.id,
                    'annee_scolaire': request.env['ersge.dossier.famille']
                                      ._get_current_school_year(),
                    'state':          'incomplet',
                })

            # ✅ Accès automatique au créateur
            new_dossier.add_acces(partner, role=my_role)

            if my_role in ['parent1', 'parent2']:
                return request.redirect(
                    f'/my/ecolage/{new_dossier.id}/acces'
                    f'?just_created=1'
                )
            else:
                return request.redirect(
                    f'/my/ecolage/edit/{new_dossier.id}'
                )

        return request.render(
            'ersge_portal_ecolage.portal_famille_create',
            {'csrf_token': request.csrf_token()},
        )

    # ==================== GESTION DES ACCÈS ====================

    @http.route(
        '/my/ecolage/<int:dossier_id>/acces',
        type='http', auth='user', website=True,
        methods=['GET', 'POST'],
    )
    def portal_dossier_acces(self, dossier_id, **kwargs):
        partner = request.env.user.partner_id
        dossier = request.env['ersge.dossier.famille'].sudo().browse(
            dossier_id
        )

        if not dossier.exists() or not self._check_dossier_access(
            dossier, partner
        ):
            return request.redirect('/my/ecolage')

        error   = None
        success = None

        # Message d'accueil après création
        just_created = kwargs.get('just_created')

        if request.httprequest.method == 'POST':
            email = kwargs.get('email', '').strip()
            role  = kwargs.get('role', 'parent2')

            if not email:
                error = "Veuillez saisir une adresse email."
            else:
                try:
                    dossier.invite_by_email(email, role=role)
                    success = f"Invitation envoyée à {email}."
                except Exception as e:
                    _logger.exception(
                        "Erreur invitation dossier %s", dossier_id
                    )
                    error = str(e)

        return request.render(
            'ersge_portal_ecolage.portal_dossier_acces',
            {
                'dossier':       dossier,
                'acces_list':    dossier.acces_ids,
                'error':         error,
                'success':       success,
                'just_created':  just_created,
                'csrf_token':    request.csrf_token(),
            },
        )

    # ==================== ACCEPTER UNE INVITATION ====================

    @http.route(
        '/my/ecolage/join/<string:token>',
        type='http', auth='public', website=True,
    )
    def portal_join_dossier(self, token, **kwargs):
        acces = request.env['ersge.dossier.acces'].sudo().search([
            ('invite_token', '=', token),
            ('invite_state', '=', 'pending'),
        ], limit=1)

        if not acces:
            return request.render(
                'ersge_portal_ecolage.portal_invite_invalid', {}
            )

        # Connecté → lier le compte
        if not request.env.user._is_public():
            partner = request.env.user.partner_id
            acces.write({
                'partner_id':   partner.id,
                'invite_state': 'accepted',
                'invite_token': False,
            })
            return request.redirect(
                f'/my/ecolage/edit/{acces.dossier_id.id}'
            )

        # Non connecté → stocker token en session + login
        request.session['invite_token'] = token
        return request.redirect(
            '/web/login?redirect=/my/ecolage/join/confirm'
        )

    @http.route(
        '/my/ecolage/join/confirm',
        type='http', auth='user', website=True,
    )
    def portal_join_confirm(self, **kwargs):
        token = request.session.get('invite_token')
        if not token:
            return request.redirect('/my/ecolage')

        acces = request.env['ersge.dossier.acces'].sudo().search([
            ('invite_token', '=', token),
            ('invite_state', '=', 'pending'),
        ], limit=1)

        if not acces:
            return request.render(
                'ersge_portal_ecolage.portal_invite_invalid', {}
            )

        partner = request.env.user.partner_id
        acces.write({
            'partner_id':   partner.id,
            'invite_state': 'accepted',
            'invite_token': False,
        })
        request.session.pop('invite_token', None)
        return request.redirect(
            f'/my/ecolage/edit/{acces.dossier_id.id}'
        )

    # ==================== RÉVOQUER UN ACCÈS ====================

    @http.route(
        '/my/ecolage/<int:dossier_id>/acces/<int:acces_id>/revoke',
        type='http', auth='user', website=True,
        methods=['POST'],
    )
    def portal_revoke_acces(self, dossier_id, acces_id, **kwargs):
        partner = request.env.user.partner_id
        dossier = request.env['ersge.dossier.famille'].sudo().browse(
            dossier_id
        )

        if not dossier.exists() or not self._check_dossier_access(
            dossier, partner
        ):
            return request.redirect('/my/ecolage')

        acces = request.env['ersge.dossier.acces'].sudo().browse(
            acces_id
        )
        if acces.exists() and acces.partner_id != partner:
            acces.unlink()

        return request.redirect(
            f'/my/ecolage/{dossier_id}/acces'
        )

    # ==================== NOUVEAU DOSSIER ====================

    @http.route('/my/ecolage/new', type='http', auth='user', website=True)
    def new_dossier(self, **kwargs):
        partner = request.env.user.partner_id
        if not partner.family_id:
            return request.redirect('/my/ecolage/family/create')

        try:
            new = request.env['ersge.dossier.famille'].sudo()\
                .with_context(
                    default_family_id=partner.family_id.id
                ).create({
                    'family_id':      partner.family_id.id,
                    'annee_scolaire': request.env['ersge.dossier.famille']
                                      ._get_current_school_year(),
                    'state':          'incomplet',
                })

            # ✅ Accès automatique au créateur
            new.add_acces(partner, role=partner.family_role or 'parent1')

            return request.redirect(f'/my/ecolage/edit/{new.id}')

        except Exception as e:
            _logger.exception("[new_dossier] ERREUR: %s", e)
            return request.render(
                'ersge_portal_ecolage.portal_my_dossiers',
                {'dossiers': [], 'error': str(e)},
            )

    # ==================== ÉDITION DU DOSSIER ====================

    @http.route(
        '/my/ecolage/edit/<int:dossier_id>',
        type='http', auth='user', website=True,
        methods=['GET', 'POST'],
    )
    def edit_dossier(self, dossier_id, **kwargs):
        try:
            partner = request.env.user.partner_id
            dossier = request.env['ersge.dossier.famille'].sudo().browse(
                dossier_id
            )

            if not dossier.exists():
                return request.redirect('/my/ecolage')

            # ✅ Vérification accès (nouvelle + ancienne logique)
            if not self._check_dossier_access(dossier, partner):
                raise AccessError(
                    "Vous n'avez pas accès à ce dossier."
                )

            if dossier.state != 'incomplet':
                return request.redirect(
                    '/my/ecolage?error=already_submitted'
                )

            if request.httprequest.method == 'POST':
                params = request.params
                form   = request.httprequest.form

                _logger.warning(
                    "========== DEBUT POST DOSSIER %s ==========",
                    dossier.id,
                )

                # ===== 1. NOUVEAUX ÉLÈVES =====
                new_firstnames  = form.getlist('new_student_firstname[]')
                new_lastnames   = form.getlist('new_student_lastname[]')
                new_birthdates  = form.getlist('new_student_birthdate[]')
                new_genders     = form.getlist('new_student_gender[]')
                raw_image_rights = form.getlist('new_student_image_rights[]')

                for i in range(len(new_firstnames)):
                    if new_firstnames[i] or new_lastnames[i]:
                        vals_ir = (
                            raw_image_rights[2 * i + 1] == '1'
                            if (2 * i + 1) < len(raw_image_rights)
                            else False
                        )
                        student = request.env['ersge.student'].sudo().create({
                            'firstname':   new_firstnames[i],
                            'lastname':    new_lastnames[i],
                            'birthdate':   new_birthdates[i] or False,
                            'gender':      new_genders[i],
                            'image_rights': vals_ir,
                            'family_id':   dossier.family_id.id,
                        })
                        request.env['ersge.dossier.student.line'].sudo().create({
                            'dossier_id': dossier.id,
                            'student_id': student.id,
                        })
                        _logger.warning(
                            "Nouvel élève: %s %s",
                            new_firstnames[i], new_lastnames[i],
                        )

                # ===== 2. MISE À JOUR ÉLÈVES EXISTANTS =====
                for key in list(params.keys()):
                    if key.startswith('student_line_id_'):
                        line_id = int(params.get(key))
                        line = request.env[
                            'ersge.dossier.student.line'
                        ].sudo().browse(line_id)
                        if line.exists() and line.dossier_id.id == dossier.id:
                            checkbox_key = f'student_image_rights_{line_id}'
                            hidden_key   = f'student_image_rights_hidden_{line_id}'
                            if checkbox_key in params:
                                image_rights = params.get(checkbox_key) == '1'
                            else:
                                image_rights = params.get(hidden_key, '0') == '1'

                            line.student_id.sudo().write({
                                'firstname':    params.get(f'student_firstname_{line_id}', ''),
                                'lastname':     params.get(f'student_lastname_{line_id}', ''),
                                'birthdate':    params.get(f'student_birthdate_{line_id}') or False,
                                'gender':       params.get(f'student_gender_{line_id}'),
                                'image_rights': image_rights,
                            })
                            forfait_key = f'forfait_id_{line_id}'
                            if forfait_key in params:
                                forfait_val = params.get(forfait_key)
                                line.sudo().write({
                                    'forfait_id': int(forfait_val) if forfait_val else False
                                })

                # ===== 3. CHAMPS SIMPLES =====
                simple_fields = [
                    'legal_representation', 'legal_representation_other',
                    'deposit_status', 'employer_assistance',
                    'send_invoice_to_employer', 'same_address_as_parent1',
                    'after_school_request', 'reduction_requested',
                    'requested_discount', 'gross_annual_income',
                    'additional_reduction_request', 'proposed_monthly_amount',
                    'contract_accepted', 'convention_accepted',
                    'procedures_accepted', 'terms_accepted', 'lpd_consent',
                    'explanatory_letter_text', 'explanatory_letter_mode',
                    'budget_method', 'apply_children_discount',
                    'apply_seniority_discount', 'seniority_years',
                ]
                dossier_vals = {}
                bool_simple = {
                    'send_invoice_to_employer', 'same_address_as_parent1',
                    'reduction_requested', 'additional_reduction_request',
                    'contract_accepted', 'convention_accepted',
                    'procedures_accepted', 'terms_accepted', 'lpd_consent',
                    'apply_children_discount', 'apply_seniority_discount',
                }
                for k in simple_fields:
                    if k in params:
                        val = params.get(k)
                        dossier_vals[k] = (val == '1') if k in bool_simple else val

                for field in ['solidarity_request', 'sponsorship_request',
                              'payment_terms']:
                    val = params.get(field)
                    if val:
                        dossier_vals[field] = val

                for field in ['apply_solidarity_increase',
                              'multi_billing_request']:
                    values = form.getlist(field)
                    if values:
                        dossier_vals[field] = values[-1] == '1'

                for field in ['address_book_optin']:
                    values = form.getlist(field)
                    if values:
                        dossier_vals[field] = values[-1] == '1'

                if params.get('solidarity_percentage'):
                    try:
                        dossier_vals['solidarity_percentage'] = float(
                            params.get('solidarity_percentage')
                        )
                    except ValueError:
                        pass

                if 'comments' in params:
                    dossier_vals['comments'] = params.get('comments')
                if 'signature_text' in params:
                    dossier_vals['signature_text'] = params.get('signature_text')

                # Facturation divisée
                try:
                    p1 = float(
                        params.get('parent1_billing_amount', '0')
                        .replace(',', '.')
                    )
                    p2 = float(
                        params.get('parent2_billing_amount', '0')
                        .replace(',', '.')
                    )
                except ValueError:
                    p1 = p2 = 0.0

                if dossier_vals.get('multi_billing_request'):
                    dossier_vals['parent1_billing_amount'] = p1
                    dossier_vals['parent2_billing_amount'] = p2
                else:
                    dossier_vals['parent1_billing_amount'] = 0.0
                    dossier_vals['parent2_billing_amount'] = 0.0

                if dossier_vals:
                    dossier.sudo().write(dossier_vals)

                # ===== 4. PARENT 1 =====
                parent1_vals = {
                    'firstname':     params.get('parent1_firstname', '').strip(),
                    'lastname':      params.get('parent1_lastname', '').strip(),
                    'email':         params.get('parent1_email', '').strip(),
                    'phone':         params.get('parent1_phone', '').strip(),
                    'phone_fixed':   params.get('parent1_phone_fixed', '').strip(),
                    'phone_pro':     params.get('parent1_phone_pro', '').strip(),
                    'street':        params.get('parent1_street', '').strip(),
                    'zip':           params.get('parent1_zip', '').strip(),
                    'city':          params.get('parent1_city', '').strip(),
                    'profession':    params.get('parent1_profession', '').strip(),
                    'employer_name': params.get('parent1_employeur', '').strip(),
                    'is_parent':     True,
                    'family_id':     dossier.family_id.id,
                    'family_role':   'parent1',
                }
                fn = f"{parent1_vals['firstname']} {parent1_vals['lastname']}".strip()
                parent1_vals['name'] = fn or parent1_vals.get('email', 'Parent 1')
                if params.get('parent1_country_id'):
                    parent1_vals['country_id'] = int(
                        params.get('parent1_country_id')
                    )

                if dossier.parent1_id:
                    dossier.parent1_id.sudo().write(parent1_vals)
                else:
                    if (partner.family_role == 'parent1'
                            and partner.family_id.id == dossier.family_id.id):
                        partner.sudo().write(parent1_vals)
                        dossier.sudo().write({'parent1_id': partner.id})
                    else:
                        existing = request.env['res.partner'].sudo().search([
                            ('firstname', '=', parent1_vals['firstname']),
                            ('lastname',  '=', parent1_vals['lastname']),
                            ('family_id', '=', dossier.family_id.id),
                        ], limit=1)
                        if existing:
                            existing.sudo().write(parent1_vals)
                            dossier.sudo().write({'parent1_id': existing.id})
                        else:
                            np1 = request.env['res.partner'].sudo().create(
                                parent1_vals
                            )
                            dossier.sudo().write({'parent1_id': np1.id})

                # ===== 5. PARENT 2 =====
                if params.get('parent2_firstname') or params.get('parent2_lastname'):
                    parent2_vals = {
                        'firstname':     params.get('parent2_firstname', ''),
                        'lastname':      params.get('parent2_lastname', ''),
                        'email':         params.get('parent2_email', ''),
                        'phone':         params.get('parent2_phone', ''),
                        'phone_fixed':   params.get('parent2_phone_fixed', ''),
                        'phone_pro':     params.get('parent2_phone_pro', ''),
                        'profession':    params.get('parent2_profession', ''),
                        'employer_name': params.get('parent2_employeur', ''),
                        'is_parent':     True,
                        'family_id':     dossier.family_id.id,
                    }
                    fn2 = f"{parent2_vals['firstname']} {parent2_vals['lastname']}".strip()
                    parent2_vals['name'] = fn2 or parent2_vals.get('email', 'Parent 2')

                    same_addr = params.get('same_address_as_parent1') == '1'
                    if same_addr and dossier.parent1_id:
                        parent2_vals.update({
                            'street':     dossier.parent1_id.street or '',
                            'zip':        dossier.parent1_id.zip or '',
                            'city':       dossier.parent1_id.city or '',
                            'country_id': (dossier.parent1_id.country_id.id
                                           if dossier.parent1_id.country_id
                                           else False),
                        })
                    else:
                        parent2_vals.update({
                            'street': params.get('parent2_street', ''),
                            'zip':    params.get('parent2_zip', ''),
                            'city':   params.get('parent2_city', ''),
                        })
                        if params.get('parent2_country_id'):
                            parent2_vals['country_id'] = int(
                                params.get('parent2_country_id')
                            )

                    if dossier.parent2_id:
                        dossier.parent2_id.sudo().write(parent2_vals)
                    else:
                        np2 = request.env['res.partner'].sudo().create(
                            parent2_vals
                        )
                        dossier.sudo().write({'parent2_id': np2.id})

                # ===== 6. AUTRE REPRÉSENTANT =====
                other_vals = {}
                for field in [
                    'other_firstname', 'other_lastname', 'other_email',
                    'other_phone', 'other_phone_fixed', 'other_phone_pro',
                    'other_street', 'other_zip', 'other_city',
                    'other_profession', 'other_employeur', 'other_country_id',
                ]:
                    if field in params:
                        val = params.get(field)
                        other_vals[field] = (
                            int(val) if field == 'other_country_id' and val
                            else (False if field == 'other_country_id'
                                  else val.strip() if isinstance(val, str)
                                  else val)
                        )
                if other_vals:
                    dossier.sudo().write(other_vals)

                # ===== 7. BUDGET EN LIGNE =====
                if params.get('budget_method') == 'online':
                    for key, value in params.items():
                        if key.startswith('montant_madame_'):
                            line_id = int(key.split('_')[-1])
                            line = request.env['ersge.budget.line'].sudo().browse(
                                line_id
                            )
                            if line.exists() and line.dossier_id.id == dossier.id:
                                line.sudo().write({
                                    'montant_madame':    float(value or 0),
                                    'montant_monsieur':  float(
                                        params.get(
                                            f'montant_monsieur_{line_id}', 0
                                        ) or 0
                                    ),
                                })

                # ===== 8. EMPLOYEUR =====
                if (params.get('employer_assistance') == 'yes'
                        and params.get('send_invoice_to_employer') == '1'):
                    employer_vals = {
                        'name':       params.get('employer_name', '') or 'Employeur',
                        'street':     params.get('employer_street', ''),
                        'zip':        params.get('employer_zip', ''),
                        'city':       params.get('employer_city', ''),
                        'country_id': (int(params.get('employer_country_id'))
                                       if params.get('employer_country_id')
                                       else False),
                        'is_employer': True,
                    }
                    existing_emp = request.env['res.partner'].sudo().search([
                        ('name', '=', employer_vals['name']),
                        ('is_employer', '=', True),
                    ], limit=1)
                    employer = (existing_emp
                                if existing_emp
                                else request.env['res.partner'].sudo().create(
                                    employer_vals
                                ))
                    dossier.sudo().write({'employer_id': employer.id})
                else:
                    dossier.sudo().write({'employer_id': False})

                # ===== 9. PARASCOLAIRE =====
                existing_after = dossier.after_school_line_ids
                for student_line in dossier.student_line_ids:
                    selected = params.get(
                        f'after_school_selected_{student_line.id}'
                    ) == '1'
                    after_line = existing_after.filtered(
                        lambda l: l.student_id.id == student_line.student_id.id
                    )
                    if selected:
                        accueil_type  = params.get(
                            f'accueil_type_{student_line.id}'
                        )
                        prestations   = request.env[
                            'ersge.after.school.prestation'
                        ].sudo().search([])
                        prestation_ids = [
                            p.id for p in prestations
                            if params.get(
                                f'prestation_{student_line.id}_{p.id}'
                            ) == '1'
                        ]
                        if after_line:
                            after_line.sudo().write({
                                'selected':       True,
                                'accueil_type':   accueil_type,
                                'prestation_ids': [(6, 0, prestation_ids)],
                            })
                        else:
                            request.env['ersge.after.school.line'].sudo().create({
                                'dossier_id':     dossier.id,
                                'student_id':     student_line.student_id.id,
                                'selected':       True,
                                'accueil_type':   accueil_type,
                                'prestation_ids': [(6, 0, prestation_ids)],
                            })
                    else:
                        if after_line:
                            after_line.sudo().unlink()

                # ===== 10. PARRAINS =====
                for key in list(params.keys()):
                    if key.startswith('sp_id_'):
                        sp_id = int(params.get(key))
                        sp = request.env['ersge.sponsorship'].sudo().browse(
                            sp_id
                        )
                        if sp.exists() and sp.dossier_id.id == dossier.id:
                            sp.sudo().write({
                                'firstname':  params.get(f'sp_firstname_{sp_id}', ''),
                                'lastname':   params.get(f'sp_lastname_{sp_id}', ''),
                                'street':     params.get(f'sp_street_{sp_id}', ''),
                                'zip':        params.get(f'sp_zip_{sp_id}', ''),
                                'city':       params.get(f'sp_city_{sp_id}', ''),
                                'country_id': (int(params.get(f'sp_country_id_{sp_id}'))
                                               if params.get(f'sp_country_id_{sp_id}')
                                               else False),
                                'amount':     float(
                                    params.get(f'sp_amount_{sp_id}') or 0
                                ),
                            })

                submitted_sp_ids = [
                    int(params.get(k))
                    for k in params.keys()
                    if k.startswith('sp_id_')
                ]
                for sp in dossier.sponsorship_ids:
                    if sp.id not in submitted_sp_ids:
                        sp.sudo().unlink()

                new_sp_firstnames  = form.getlist('new_sp_firstname[]')
                new_sp_lastnames   = form.getlist('new_sp_lastname[]')
                new_sp_streets     = form.getlist('new_sp_street[]')
                new_sp_zips        = form.getlist('new_sp_zip[]')
                new_sp_cities      = form.getlist('new_sp_city[]')
                new_sp_country_ids = form.getlist('new_sp_country_id[]')
                new_sp_amounts     = form.getlist('new_sp_amount[]')

                for i in range(len(new_sp_firstnames)):
                    if new_sp_firstnames[i] or new_sp_lastnames[i]:
                        request.env['ersge.sponsorship'].sudo().create({
                            'dossier_id': dossier.id,
                            'firstname':  new_sp_firstnames[i],
                            'lastname':   new_sp_lastnames[i],
                            'street':     new_sp_streets[i] if i < len(new_sp_streets) else '',
                            'zip':        new_sp_zips[i] if i < len(new_sp_zips) else '',
                            'city':       new_sp_cities[i] if i < len(new_sp_cities) else '',
                            'country_id': (int(new_sp_country_ids[i])
                                           if i < len(new_sp_country_ids)
                                           and new_sp_country_ids[i]
                                           else False),
                            'amount':     (float(new_sp_amounts[i])
                                           if i < len(new_sp_amounts)
                                           and new_sp_amounts[i]
                                           else 0.0),
                        })

                # ===== REDIRECTION FINALE =====
                if params.get('form_action') == 'save_and_stay':
                    return request.redirect(
                        f'/my/ecolage/edit/{dossier.id}'
                    )
                elif params.get('form_action') == 'submit_dossier':
                    dossier.sudo().write({
                        'state':            'soumis',
                        'date_soumission':  fields.Datetime.now(),
                    })
                    return request.redirect(
                        '/my/ecolage?success=1&submitted=1'
                    )
                return request.redirect('/my/ecolage?success=1')

            # ==================== GET ====================
            prefill_firstname = partner.firstname or ''
            prefill_lastname  = (partner.lastname or partner.name or '')

            prefill_parent1 = {}
            if not dossier.parent1_id and partner.family_role in [
                'parent1', 'parent2'
            ]:
                prefill_parent1 = {
                    'firstname':   prefill_firstname,
                    'lastname':    prefill_lastname,
                    'email':       partner.email or '',
                    'phone':       partner.phone or '',
                    'phone_fixed': getattr(partner, 'phone_fixed', '') or '',
                    'phone_pro':   getattr(partner, 'phone_pro', '') or '',
                    'street':      partner.street or '',
                    'zip':         partner.zip or '',
                    'city':        partner.city or '',
                }

            prefill_parent2 = {}
            if not dossier.parent2_id and partner.family_role == 'parent2':
                prefill_parent2 = {
                    'firstname':   prefill_firstname,
                    'lastname':    prefill_lastname,
                    'email':       partner.email or '',
                    'phone':       partner.phone or '',
                    'phone_fixed': getattr(partner, 'phone_fixed', '') or '',
                    'phone_pro':   getattr(partner, 'phone_pro', '') or '',
                    'street':      partner.street or '',
                    'zip':         partner.zip or '',
                    'city':        partner.city or '',
                }

            prefill_tutor = {}
            if not dossier.parent1_id and partner.family_role == 'tutor':
                prefill_tutor = {
                    'firstname':   prefill_firstname,
                    'lastname':    prefill_lastname,
                    'email':       partner.email or '',
                    'phone':       partner.phone or '',
                    'phone_fixed': getattr(partner, 'phone_fixed', '') or '',
                    'phone_pro':   getattr(partner, 'phone_pro', '') or '',
                    'street':      partner.street or '',
                    'zip':         partner.zip or '',
                    'city':        partner.city or '',
                }

            countries  = request.env['res.country'].sudo().search([])
            forfaits   = request.env['ersge.forfait'].sudo().search([
                ('active', '=', True)
            ])
            after_school_prestations = request.env[
                'ersge.after.school.prestation'
            ].sudo().search([('active', '=', True)])

            return request.render(
                'ersge_portal_ecolage.portal_dossier_form_complete',
                {
                    'dossier':                  dossier,
                    'prefill_parent1':          prefill_parent1,
                    'prefill_parent2':          prefill_parent2,
                    'prefill_tutor':            prefill_tutor,
                    'csrf_token':               request.csrf_token(),
                    'countries':                countries,
                    'forfaits':                 forfaits,
                    'after_school_prestations': after_school_prestations,
                },
            )

        except AccessError:
            raise
        except Exception as e:
            _logger.exception("[edit_dossier] ERREUR: %s", e)
            return request.redirect('/my/ecolage')

    # ==================== SUPPRESSION LIGNE ÉLÈVE (AJAX) ====================

    @http.route(
        '/my/ecolage/delete_student_line',
        type='json', auth='user', methods=['POST'], csrf=True,
    )
    def delete_student_line(self):
        data    = request.get_json_data()
        line_id = data.get('line_id')
        if not line_id:
            return {'success': False, 'error': 'ID manquant'}
        try:
            line    = request.env['ersge.dossier.student.line'].sudo().browse(
                int(line_id)
            )
            if not line.exists():
                return {'success': False, 'error': 'Ligne introuvable'}

            partner = request.env.user.partner_id
            dossier = line.dossier_id

            if self._check_dossier_access(dossier, partner):
                dossier.sudo().write({'requested_discount': 0.0})
                line.unlink()
                return {'success': True}
            else:
                return {'success': False, 'error': 'Accès non autorisé'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ==================== CONSULTATION ====================

    @http.route(
        '/my/ecolage/dossier/<int:dossier_id>',
        type='http', auth='user', website=True,
    )
    def view_dossier(self, dossier_id, **kwargs):
        partner = request.env.user.partner_id
        dossier = request.env['ersge.dossier.famille'].sudo().browse(
            dossier_id
        )
        if not dossier.exists():
            return request.redirect('/my/ecolage')

        if not self._check_dossier_access(dossier, partner):
            return request.redirect('/my/ecolage')

        countries = request.env['res.country'].sudo().search([])
        return request.render(
            'ersge_portal_ecolage.portal_dossier_view',
            {'dossier': dossier, 'countries': countries},
        )

    # ==================== SUPPRESSION DOSSIER ====================

    @http.route(
        '/my/ecolage/delete/<int:dossier_id>',
        type='http', auth='user', website=True, methods=['POST'],
    )
    def delete_dossier(self, dossier_id):
        partner = request.env.user.partner_id
        dossier = request.env['ersge.dossier.famille'].sudo().browse(
            dossier_id
        )

        if not dossier.exists():
            return request.redirect(
                '/my/ecolage?error=Dossier introuvable'
            )
        if not self._check_dossier_access(dossier, partner):
            return request.redirect(
                '/my/ecolage?error=Accès non autorisé'
            )
        if dossier.state == 'soumis':
            return request.redirect(
                '/my/ecolage?error=Impossible de supprimer un dossier déjà soumis'
            )

        try:
            dossier.unlink()
            return request.redirect(
                '/my/ecolage?success=Dossier supprimé avec succès'
            )
        except Exception as e:
            return request.redirect(
                f'/my/ecolage?error=Erreur lors de la suppression : {str(e)}'
            )

    # ==================== REDIRECTIONS LEGACY ====================

    @http.route('/my/famille/new', type='http', auth='user', website=True,
                methods=['GET', 'POST'])
    def famille_new(self, **kwargs):
        return request.redirect('/my/ecolage/family/create')

    @http.route('/my/ecolage/invite', type='http', auth='user', website=True,
                methods=['GET', 'POST'])
    def invite_partner_legacy(self, **kwargs):
        """Ancienne route d'invitation — redirige vers la nouvelle."""
        dossier_id = kwargs.get('dossier_id')
        if dossier_id:
            return request.redirect(
                f'/my/ecolage/{dossier_id}/acces'
            )
        return request.redirect('/my/ecolage')