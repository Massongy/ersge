from odoo import models, fields

class ErsgeSponsor(models.Model):
    _name = 'ersge.sponsorship'
    _description = 'Parrain'

    dossier_id = fields.Many2one('ersge.dossier.famille', string='Dossier', ondelete='cascade')
    firstname = fields.Char(string='Prénom', required=True)
    lastname = fields.Char(string='Nom', required=True)
    street = fields.Char(string='Adresse')
    zip = fields.Char(string='Code Postal')
    city = fields.Char(string='Ville')
    country_id = fields.Many2one('res.country', string='Pays')
    amount = fields.Float(string='Montant /mois (CHF)')