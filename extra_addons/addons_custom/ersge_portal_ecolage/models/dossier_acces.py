# -*- coding: utf-8 -*-
import secrets
import logging
from odoo import models, fields

_logger = logging.getLogger(__name__)


class ErsgeDossierAcces(models.Model):
    _name = 'ersge.dossier.acces'
    _description = "Accès d'un compte portal à un dossier"
    _rec_name = 'partner_id'

    dossier_id = fields.Many2one(
        'ersge.dossier.famille',
        string='Dossier',
        required=True,
        ondelete='cascade',
        index=True,
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Compte portal',
        ondelete='cascade',
        index=True,
    )
    role = fields.Selection([
        ('parent1', 'Parent 1'),
        ('parent2', 'Parent 2'),
        ('tutor',   'Tuteur / Autre'),
    ], string='Rôle', required=True, default='parent2')

    invite_token = fields.Char(
        string="Token d'invitation",
        index=True,
        copy=False,
    )
    invite_email = fields.Char(string='Email invité')
    invite_state = fields.Selection([
        ('pending',  'En attente'),
        ('accepted', 'Acceptée'),
    ], string='État', default='pending')
    invite_date = fields.Datetime(string="Date d'invitation")

    _sql_constraints = [
        (
            'unique_partner_dossier',
            'UNIQUE(partner_id, dossier_id)',
            'Ce compte a déjà accès à ce dossier.',
        ),
    ]

    def generate_token(self):
        self.write({
            'invite_token': secrets.token_urlsafe(32),
            'invite_date': fields.Datetime.now(),
        })
        return self.invite_token

    def get_invite_url(self):
        base = self.env['ir.config_parameter'].sudo().get_param(
            'web.base.url'
        )
        return f"{base}/my/ecolage/join/{self.invite_token}"

    def send_invite_email(self):
        url = self.get_invite_url()
        dossier = self.dossier_id
        famille = dossier.family_id

        role_labels = {
            'parent1': 'Parent 1',
            'parent2': 'Parent 2',
            'tutor':   'Tuteur / Autre',
        }
        role_label = role_labels.get(self.role, self.role)
        dest_email = self.invite_email or (
            self.partner_id.email if self.partner_id else None
        )

        if not dest_email:
            _logger.warning(
                "Invitation sans email pour l'accès %s", self.id
            )
            return

        famille_name = famille.name if famille else dossier.name
        subject = (
            f"Invitation à accéder au dossier d'écolage "
            f"— Famille {famille_name}"
        )
        body = f"""
            <p>Bonjour,</p>
            <p>
                Vous avez été invité(e) à accéder au dossier d'écolage
                de la famille <strong>{famille_name}</strong>
                en tant que <strong>{role_label}</strong>.
            </p>
            <p>Cliquez sur le bouton ci-dessous pour accepter :</p>
            <p>
                <a href="{url}" style="
                    background:#1a3a5c;color:white;
                    padding:10px 20px;border-radius:4px;
                    text-decoration:none;font-weight:bold;
                ">
                    Accéder au dossier
                </a>
            </p>
            <p style="color:#888;font-size:0.85em;">
                Si vous n'avez pas encore de compte sur le portail,
                vous serez invité(e) à en créer un gratuitement.<br/>
                Lien direct : {url}
            </p>
        """
        mail = self.env['mail.mail'].sudo().create({
            'subject': subject,
            'body_html': body,
            'email_to': dest_email,
        })
        mail.send()
        _logger.info(
            "Invitation envoyée à %s pour le dossier %s",
            dest_email, dossier.name,
        )