# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.tools.misc import formatLang, format_date, get_lang

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


    @api.depends('line_ids.price_subtotal', 'line_ids.tax_base_amount', 'line_ids.tax_line_id', 'partner_id', 'currency_id')
    def _compute_invoice_taxes_by_group(self):
        ''' Helper to get the taxes grouped according their account.tax.group.
        This method is only used when printing the invoice.
        '''
        for move in self:
            lang_env = move.with_context(lang=move.partner_id.lang).env
            tax_lines = move.line_ids.filtered(lambda line: line.tax_line_id)
            tax_balance_multiplicator = -1 if move.is_inbound(True) else 1
            res = {}
            # There are as many tax line as there are repartition lines
            done_taxes = set()
            for line in tax_lines:
                res.setdefault(line.tax_line_id.tax_group_id, {'base': 0.0, 'amount': 0.0})
                res[line.tax_line_id.tax_group_id]['amount'] += tax_balance_multiplicator * (line.amount_currency if line.currency_id else line.balance)
                tax_key_add_base = tuple(move._get_tax_key_for_group_add_base(line))



                #TODO : J'ai modifié les lignes ci-dessous le 22/04/2021, car il y avait un bug
                if tax_key_add_base not in done_taxes:
                    # The base should be added ONCE
                    done_taxes.add(tax_key_add_base)

                if line.currency_id and line.company_currency_id and line.currency_id != line.company_currency_id:
                    amount = line.company_currency_id._convert(line.tax_base_amount, line.currency_id, line.company_id, line.date or fields.Date.context_today(self))
                else:
                    amount = line.tax_base_amount
                res[line.tax_line_id.tax_group_id]['base'] += amount
                #**************************************************************


            # At this point we only want to keep the taxes with a zero amount since they do not
            # generate a tax line.
            zero_taxes = set()
            for line in move.line_ids:
                for tax in line.tax_ids.flatten_taxes_hierarchy():
                    if tax.tax_group_id not in res or tax.tax_group_id in zero_taxes:
                        res.setdefault(tax.tax_group_id, {'base': 0.0, 'amount': 0.0})
                        res[tax.tax_group_id]['base'] += tax_balance_multiplicator * (line.amount_currency if line.currency_id else line.balance)
                        zero_taxes.add(tax.tax_group_id)

            res = sorted(res.items(), key=lambda l: l[0].sequence)
            move.amount_by_group = [(
                group.name, amounts['amount'],
                amounts['base'],
                formatLang(lang_env, amounts['amount'], currency_obj=move.currency_id),
                formatLang(lang_env, amounts['base'], currency_obj=move.currency_id),
                len(res),
                group.id
            ) for group, amounts in res]






class AccountMoveLine(models.Model):
    _inherit = "account.move.line"
    #_order = "invoice_id,id"

    is_num_controle = fields.Char(string="N° du contrôle")


