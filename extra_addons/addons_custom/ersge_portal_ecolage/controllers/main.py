# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.exceptions import AccessError
import logging

_logger = logging.getLogger(__name__)


class PortalEcolage(http.Controller):

    def _get_partner_family(self, partner):
        """Retourne la famille du partenaire connecté via family_id sur res.partner"""
        return request.env['ersge.family'].sudo().search([
            ('parent_ids', 'in', [partner.id])
        ], limit=1)

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

    @http.route('/my/ecolage/new', type='http', auth='user', website=True)
    def new_dossier(self, **kwargs):
        try:
            partner = request.env.user.partner_id
            _logger.warning(f"[new_dossier] partner={partner.id} ({partner.name})")

            family = self._get_partner_family(partner)
            _logger.warning(f"[new_dossier] family={family.id if family else None}")

            if not family:
                return request.render('ersge_portal_ecolage.portal_my_dossiers', {
                    'dossiers': [],
                    'error': "Vous n'êtes rattaché à aucune famille. Contactez l'administrateur.",
                })

            new = request.env['ersge.dossier.famille'].sudo().with_context(
                default_family_id=family.id
            ).create({
                'family_id': family.id,
                'annee_scolaire': request.env['ersge.dossier.famille']._get_current_school_year(),
                'state': 'incomplet',
            })

            _logger.warning(f"[new_dossier] dossier créé id={new.id}")
            return request.redirect(f'/my/ecolage/edit/{new.id}')

        except Exception as e:
            _logger.exception(f"[new_dossier] ERREUR: {e}")
            return request.render('ersge_portal_ecolage.portal_my_dossiers', {
                'dossiers': [],
                'error': f"Une erreur est survenue : {str(e)}",
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