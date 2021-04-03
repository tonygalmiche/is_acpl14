# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class AccountMove(models.Model):
    _inherit = "account.move"

    is_date_intervention = fields.Char(string="Date(s) d'intervention(s)")
    is_type_facture      = fields.Selection([
        ('atelier', 'Atelier'),
        ('controle-analogique', 'Contrôle analogique'),
        ('controle-numerique' , 'Contrôle numérique'),
        ('divers', 'Divers'),
    ], "Type de facture", required=True, default='atelier')
    is_plaque_immatriculation = fields.Char(string="Plaque d'immatriculation")
    is_kilometrage = fields.Integer(string="Kilométrage")


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"
    #_order = "invoice_id,id"

    is_num_controle = fields.Char(string="N° du contrôle")


