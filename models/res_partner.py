# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ResPartner(models.Model):
    _inherit = "res.partner"


    @api.depends('property_account_receivable_id','property_account_payable_id')
    def _compute(self):
        for obj in self:
            obj.is_code_client      = obj.property_account_receivable_id.code
            obj.is_code_fournisseur = obj.property_account_payable_id.code

    is_code_client      = fields.Char('Code Client'     , compute='_compute', store=True, readonly=True)
    is_code_fournisseur = fields.Char('Code Fournisseur', compute='_compute', store=True, readonly=True)

