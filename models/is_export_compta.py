# -*- coding: utf-8 -*-
from odoo import models,fields,api
from odoo.tools.translate import _
import datetime
from odoo.exceptions import Warning
import base64


class is_export_compta(models.Model):
    _name='is.export.compta'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = "Export en compta"
    _order='name desc'

    name               = fields.Char("N°Folio"      , readonly=True)
    type_interface     = fields.Selection([('ventes', u'Ventes'),('achats', u'Achats')], "Interface", required=True)
    date_debut         = fields.Date("Date de début")
    date_fin           = fields.Date("Date de fin")
    num_debut          = fields.Char("N° facture début")
    num_fin            = fields.Char("N° facture fin")

    ligne_ids          = fields.One2many('is.export.compta.ligne', 'export_compta_id', u'Lignes')


    _defaults = {
        'type_interface':  'ventes',
    }


    @api.model
    def create(self, vals):
        data_obj = self.env['ir.model.data']
        sequence_ids = data_obj.search([('name','=','is_export_compta_seq')])
        if sequence_ids:
            sequence_id = data_obj.browse(sequence_ids[0].id).res_id
            vals['name'] = self.env['ir.sequence'].get_id(sequence_id, 'id')
        res = super(is_export_compta, self).create(vals)
        return res


    def action_envoi_mail(self):
        body_html=u"""
        <html>
          <head>
            <meta content="text/html; charset=UTF-8" http-equiv="Content-Type">
          </head>
          <body>
            <font>Bonjour, </font>
            <br><br>
            <font>Ci-joint le fichier</font>
          </body>
        </html>
        """
        for obj in self:
            user  = self.env['res.users'].browse(self._uid)
            email = user.email
            nom   = user.name
            if email==False:
                raise Warning(u"Votre mail n'est pas renseigné !")
            if email:
                attachment_id = self.env['ir.attachment'].search([
                    ('res_model','=','is.export.compta'),
                    ('res_id'   ,'=',obj.id),
                    ('name'     ,'=','export-compta.txt')
                ])
                email_vals = {}
                email_vals.update({
                    'subject'       : 'Export compta Odoo',
                    'email_to'      : email, 
                    'email_from'    : email, 
                    'body_html'     : body_html.encode('utf-8'), 
                    'attachment_ids': [(6, 0, [attachment_id.id])] 
                })
                email_id=self.env['mail.mail'].create(email_vals)
                if email_id:
                    self.env['mail.mail'].send(email_id)


    def action_export_compta(self):
        cr=self._cr
        for obj in self:
            obj.ligne_ids.unlink()
            if obj.type_interface=='ventes':
                type_facture=['out_invoice', 'out_refund']
                journal='70'
            else:
                type_facture=['in_invoice', 'in_refund']
                journal='AC'
            filter=[
                ('state'       , 'in' , ['posted']),
                ('move_type'   , 'in' , type_facture)
            ]
            if obj.date_debut:
                filter.append(('invoice_date', '>=', obj.date_debut))
            if obj.date_fin:
                filter.append(('invoice_date', '<=', obj.date_fin))
            if obj.num_debut:
                filter.append(('name', '>=', obj.num_debut))
            if obj.num_fin:
                filter.append(('name', '<=', obj.num_fin))
            invoices = self.env['account.move'].search(filter, order="invoice_date,id")
            if len(invoices)==0:
                raise Warning('Aucune facture à traiter')
            for invoice in invoices:
                sql="""
                    SELECT  
                        am.invoice_date,
                        am.invoice_date_due,
                        aa.code, 
                        am.name, 
                        rp.name, 
                        am.move_type, 
                        rp.is_code_client,
                        am.payment_reference,
                        sum(aml.debit), 
                        sum(aml.credit)
                    FROM account_move_line aml inner join account_move am                on aml.move_id=am.id
                                               inner join account_account aa             on aml.account_id=aa.id
                                               inner join res_partner rp                 on am.partner_id=rp.id
                    WHERE am.id="""+str(invoice.id)+""" 
                    GROUP BY am.invoice_date, am.name, rp.name, aa.code, am.move_type,rp.is_code_client, am.invoice_date_due, am.payment_reference
                    ORDER BY am.invoice_date, am.name, rp.name, aa.code, am.move_type,rp.is_code_client, am.invoice_date_due, am.payment_reference
                """
                cr.execute(sql)
                for row in cr.fetchall():
                    compte=str(row[2])
                    if obj.type_interface=='ventes' and compte=='411100':
                        compte=str(row[6])
                    piece=row[3]
                    if obj.type_interface=='achats':
                        piece=row[7]
                    if row[8]!=0.0 or row[9]!=0.0:
                        vals={
                            'export_compta_id'  : obj.id,
                            'date_facture'      : row[0],
                            'date_echeance'     : row[1],
                            'journal'           : journal,
                            'compte'            : compte,
                            'libelle'           : row[4],
                            'debit'             : row[8],
                            'credit'            : row[9],
                            'devise'            : 'E',
                            'piece'             : piece,
                            'commentaire'       : False,
                        }
                        self.env['is.export.compta.ligne'].create(vals)
            self.generer_fichier()


    def generer_fichier(self):
        for obj in self:
            model='is.export.compta'
            attachments = self.env['ir.attachment'].search([('res_model','=',model),('res_id','=',obj.id)])
            attachments.unlink()
            name='export-compta.txt'
            dest     = '/tmp/'+name
            f = open(dest,'w', encoding="ISO-8859-15")
            lig=0
            for row in obj.ligne_ids:
                lig=lig+1
                compte=str(row.compte)
                if compte=='None':
                    compte=''
                debit=row.debit
                credit=row.debit
                if row.credit>0.0:
                    montant=row.credit  
                    sens='C'
                else:
                    montant=row.debit  
                    sens='D'
                montant=(u'000000000000'+'%0.2f' % montant)[-12:]
                date_facture=row.date_facture
                date_facture=date_facture.strftime('%d%m%y')
                date_echeance=row.date_echeance
                date_echeance=date_echeance.strftime('%d%m%y')
                libelle=(row.libelle+'                    ')[0:20]
                piece=(row.piece[-8:]+'        ')[0:8]
                journal=row.journal
                f.write(str(lig))
                f.write(',')
                f.write(date_facture)
                f.write(',')
                f.write(journal)
                f.write(',')
                f.write(compte)
                f.write(',')
                f.write(',')
                f.write('"'+libelle+'"')
                f.write(',')
                f.write('"'+piece+'"')
                f.write(',')
                f.write(montant)
                f.write(',')
                f.write(sens)
                f.write(',')
                f.write(date_echeance)
                f.write(',')
                f.write('EUR')
                f.write('\r\n')
            f.close()
            r = open(dest,'rb').read()
            vals = {
                'name':        name,
                'type':        'binary',
                'res_model':   model,
                'res_id':      obj.id,
                'datas':       base64.encodebytes(r),
            }
            id = self.env['ir.attachment'].create(vals)


class is_export_compta_ligne(models.Model):
    _name = 'is.export.compta.ligne'
    _description = "Lignes d'export en compta"
    _order='date_facture,id'

    export_compta_id = fields.Many2one('is.export.compta', 'Export Compta', required=True)
    date_facture     = fields.Date("Date")
    date_echeance    = fields.Date("Date échéance")
    journal          = fields.Char("Journal")
    compte           = fields.Char("N°Compte")
    piece            = fields.Char("Pièce")
    libelle          = fields.Char("Libellé")
    debit            = fields.Float("Débit")
    credit           = fields.Float("Crédit")
    devise           = fields.Char("Devise")
    commentaire      = fields.Char("Commentaire")

    _defaults = {
        'journal': 'VTE',
        'devise' : 'E',
    }

