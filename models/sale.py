# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = "sale.order"

    is_lieu_intervention = fields.Char(string="Lieu d'intervention", help="Champ à renseigner en cas de dépannage sur site")
    is_date_intervention = fields.Date(string="Date d'intervention")


