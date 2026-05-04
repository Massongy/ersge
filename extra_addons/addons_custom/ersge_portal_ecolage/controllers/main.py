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
        user = request.env.user
        dossiers = request.env['ersge.dossier.famille'].sudo().search([
            '|',
            ('parent1_id', '=', user.partner_id.id),
            ('parent2_id', '=', user.partner_id.id),
        ])
        return request.render('ersge_portal_ecolage.portal_my_dossiers', {
            'dossiers': dossiers,
            'error': kwargs.get('error'),
        })

    @http.route('/my/ecolage/edit/<int:dossier_id>', type='http', auth='user', website=True)
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

            if request.httprequest.method == 'POST':
                vals = {k: v for k, v in request.params.items() if k != 'csrf_token'}
                dossier.sudo().write(vals)
                return request.redirect('/my/ecolage?success=1')

            return request.render('ersge_portal_ecolage.portal_dossier_form_complete', {
                'dossier': dossier,
                'csrf_token': request.csrf_token(),
            })

        except AccessError:
            raise
        except Exception as e:
            _logger.exception(f"[edit_dossier] ERREUR: {e}")
            return request.redirect('/my/ecolage')