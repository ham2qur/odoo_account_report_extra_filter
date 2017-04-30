# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from xlwt import Workbook, easyxf
from openerp.exceptions import Warning
from datetime import timedelta, datetime
import calendar
import json
from openerp.tools import config


# class FalReportAccountTypeManager(models.TransientModel):
#     _name = 'fal.report.account.type.manager'
#     _description = 'manages account type'

#     account_type_ids = fields.Many2many('account.account.type', relational="account_report_context_fal_account_type_rel")

#     @api.multi
#     def get_available_account_type_ids_and_names(self):
#         return [[at.id, at.name] for at in self.env['account.account.type'].search([])]

# #end of FalAccountReportAccountTypeManager()


class FalAccountReportAnalyticAccountManager(models.TransientModel):
    _name = 'fal.account.report.analytic.account.manager'
    _description = 'manages analytic account for reports'

    analytic_account_ids = fields.Many2many('account.analytic.account', relation='account_report_context_analytic_account')
    available_analytic_account_ids = fields.Many2many('account.analytic.account', relation="account_report_context_available_analytic_account")
    customer_ids = fields.Many2many('res.partner', relation='account_report_context_customer')
    available_customer_ids = fields.Many2many('res.partner', relation="account_report_context_available_customer")
    business_unit_ids = fields.Many2many('fal.business.unit', relation='account_report_context_business_unit')
    available_business_unit_ids = fields.Many2many('fal.business.unit', relation="account_report_context_available_business_unit")

    @api.multi
    def get_available_analytic_account_ids_and_names(self):
        analytic_account_list = []
        for aa in self.env['account.analytic.account'].search([]):
            string = ''
            if aa.code:
                string += '[' + (aa.code and aa.code.encode(encoding='utf-8', errors="ignore") or 'Name Fault') + ']'
            string += (aa.name and aa.name.encode(encoding='utf-8', errors="ignore") or '-')
            analytic_account_list.append([aa.id, string])
        return analytic_account_list

    @api.multi
    def get_available_customer_ids_and_names(self):
        return [[aa.id, aa.name] for aa in self.env['res.partner'].search([('customer', '=', True)])]

    @api.multi
    def get_available_business_unit_ids_and_names(self):
        return [[aa.id, aa.name] for aa in self.env['fal.business.unit'].search([])]

# end of FalAccountReportAnalyticAccountManager()


class AccountReportContextCommon(models.TransientModel):
    # _inherits = {'fal.report.account.type.manager': 'fal_account_type_manager_id'}
    _inherit = 'account.report.context.common'
    _inherits = {'fal.account.report.analytic.account.manager': 'fal_analytic_account_manager_id'}

    # fal_account_type_manager_id = fields.Many2one('fal.report.account.type.manager', string='Fal Account Type Manager', required=True, ondelete='cascade')
    fal_analytic_account_manager_id = fields.Many2one('fal.account.report.analytic.account.manager', string='Analytic Account Manager', required=True, ondelete='cascade')

    # Tries to find the corresponding context (model name and id) and creates it if none is found.
    @api.model
    def return_context(self, report_model, given_context, report_id=None):
        res = super(AccountReportContextCommon, self).return_context(report_model, given_context, report_id)
        res_obj = self.env[res[0]].browse(res[1])
        update = {}
        for field in given_context:
            if self._fields.get(field) and given_context[field] != 'undefined':
                if field in ['analytic_account_ids']:  # Needs to be treated differently as they are many2many
                    update[field] = [(6, 0, [int(id) for id in given_context[field]])]
                elif field in ['customer_ids']:  # Needs to be treated differently as they are many2many
                    update[field] = [(6, 0, [int(id) for id in given_context[field]])]
                elif field in ['business_unit_ids']:  # Needs to be treated differently as they are many2many
                    update[field] = [(6, 0, [int(id) for id in given_context[field]])]
                else:
                    update[field] = given_context[field]
        if update:
            res_obj.write(update)
        return res

    @api.multi
    def get_html_and_data(self, given_context=None):
        if given_context is None:
            given_context = {}
        result = {}
        if given_context:
            update = {}
            for field in given_context:
                if field.startswith('add_'):
                    update[field[4:]] = [(4, int(given_context[field]))]
                if field.startswith('remove_'):
                    update[field[7:]] = [(3, int(given_context[field]))]
                if self._fields.get(field) and given_context[field] != 'undefined':
                    if given_context[field] == 'false':
                        given_context[field] = False
                    if given_context[field] == 'none':
                        given_context[field] = None
                    if field == 'company_ids':  # Needs to be treated differently as it's a many2many
                        update[field] = [(6, 0, given_context[field])]
                    elif field == 'analytic_account_ids':
                        given_context[field] = [int(account_analytic) for account_analytic in given_context[field]]
                        update[field] = [(6, 0, given_context[field])]
                    elif field == 'customer_ids':
                        given_context[field] = [int(account_analytic) for account_analytic in given_context[field]]
                        update[field] = [(6, 0, given_context[field])]
                    elif field == 'business_unit_ids':
                        given_context[field] = [int(account_analytic) for account_analytic in given_context[field]]
                        update[field] = [(6, 0, given_context[field])]
                    else:
                        update[field] = given_context[field]

            self.write(update)
            if 'force_account' in given_context and (not self.date_from or self.date_from == self.date_to):
                self.date_from = self.env.user.company_id.compute_fiscalyear_dates(datetime.strptime(self.date_to, "%Y-%m-%d"))['date_from']
                self.date_filter = 'custom'
        lines = self.get_report_obj().get_lines(self)
        rcontext = {
            'res_company': self.env['res.users'].browse(self.env.uid).company_id,
            'context': self,
            'report': self.get_report_obj(),
            'lines': lines,
            'mode': 'display',
        }
        result['html'] = self.env['ir.model.data'].xmlid_to_object(self.get_report_obj().get_template()).render(rcontext)
        result['report_type'] = self.get_report_obj().get_report_type()
        select = ['id', 'date_filter', 'date_filter_cmp', 'date_from', 'date_to', 'periods_number', 'date_from_cmp', 'date_to_cmp', 'cash_basis', 'all_entries', 'company_ids', 'multi_company']
        result['report_context'] = self.read(select)[0]
        result['xml_export'] = self.env['account.financial.html.report.xml.export'].is_xml_export_available(self.get_report_obj())
        result['fy'] = {
            'fiscalyear_last_day': self.env.user.company_id.fiscalyear_last_day,
            'fiscalyear_last_month': self.env.user.company_id.fiscalyear_last_month,
        }
        result['available_companies'] = self.multicompany_manager_id.get_available_company_ids_and_names()
        result['available_analytic_account_ids'] = self.fal_analytic_account_manager_id.get_available_analytic_account_ids_and_names()
        result['available_customer_ids'] = self.fal_analytic_account_manager_id.get_available_customer_ids_and_names()
        result['available_business_unit_ids'] = self.fal_analytic_account_manager_id.get_available_business_unit_ids_and_names()
        return result

# end of AccountReportContextCommon()


class AccountFinancialReportContext(models.TransientModel):
    _inherits = {'fal.account.report.analytic.account.manager': 'fal_analytic_account_manager_id'}
    _inherit = "account.financial.html.report.context"

    @api.multi
    def get_html_and_data(self, given_context=None):
        result = super(AccountFinancialReportContext, self).get_html_and_data(given_context=given_context)
        result['analytic_account_ids'] = [[at.id, at.name] for at in self.fal_analytic_account_manager_id.analytic_account_ids]
        result['available_analytic_account_ids'] = self.fal_analytic_account_manager_id.get_available_analytic_account_ids_and_names()
        result['customer_ids'] = [[at.id, at.name] for at in self.fal_analytic_account_manager_id.customer_ids]
        result['available_customer_ids'] = self.fal_analytic_account_manager_id.get_available_customer_ids_and_names()
        result['business_unit_ids'] = [[at.id, at.name] for at in self.fal_analytic_account_manager_id.business_unit_ids]
        result['available_business_unit_ids'] = self.fal_analytic_account_manager_id.get_available_business_unit_ids_and_names()
        result['report_context']['analytic_account_ids'] = result['analytic_account_ids']
        result['report_context']['available_analytic_account_ids'] = result['available_analytic_account_ids']
        result['report_context']['customer_ids'] = result['customer_ids']
        result['report_context']['available_customer_ids'] = result['available_customer_ids']
        result['report_context']['business_unit_ids'] = result['business_unit_ids']
        result['report_context']['available_business_unit_ids'] = result['available_business_unit_ids']

        return result

    # @api.multi
    # def get_html_and_data(self, given_context=None):
    #     result = super(AccountFinancialReportContext, self).get_html_and_data(given_context=given_context)
    #     result['fal_account_type_ids'] = [[at.id, at.name] for at in self.account_type_ids]
    #     result['fal_available_account_type_ids'] = self.fal_account_type_manager_id.get_available_account_type_ids_and_names()
    #     result['report_context']['fal_account_type_ids'] = result['fal_account_type_ids']
    #     result['report_context']['fal_available_account_type_ids'] = result['fal_available_account_type_ids']
    #     print result['report_context']

    #     return result
# end of AccountFinancialReportContext


class ReportAccountFinancialReport(models.Model):
    _inherit = "account.financial.html.report"

    @api.multi
    def get_lines(self, context_id, line_id=None):
        if isinstance(context_id, int):
            context_id = self.env['account.financial.html.report.context'].browse(context_id)
        line_obj = self.line_ids
        if line_id:
            line_obj = self.env['account.financial.html.report.line'].search([('id', '=', line_id)])
        if context_id.comparison:
            line_obj = line_obj.with_context(periods=context_id.get_cmp_periods())
        used_currency = self.env.user.company_id.currency_id
        currency_table = {}
        for company in self.env['res.company'].search([]):
            if company.currency_id != used_currency:
                currency_table[company.currency_id.id] = used_currency.rate / company.currency_id.rate
        linesDicts = [{} for _ in context_id.get_periods()]
        line_obj_pnl_bs = []
        line_obj_cfs = []
        for line_obj_id in line_obj:
            if line_obj_id.financial_report_id == self.env.ref('account_reports.account_financial_report_cashsummary0') and line_obj_id.code not in ('CASHSTART', 'CASHEND'):
                line_obj_cfs.append(line_obj_id.id)
            else:
                line_obj_pnl_bs.append(line_obj_id.id)
        line_obj_pnl_bs = self.env['account.financial.html.report.line'].browse(line_obj_pnl_bs)
        line_obj_cfs = self.env['account.financial.html.report.line'].browse(line_obj_cfs)
        res = line_obj_pnl_bs.with_context(
            state=context_id.all_entries and 'all' or 'posted',
            cash_basis=self.report_type == 'date_range_cash' or context_id.cash_basis,
            strict_range=self.report_type == 'date_range_extended',
            aged_balance=self.report_type == 'date_range_extended',
            company_ids=context_id.company_ids.ids,
            account_analytic_ids=context_id.fal_analytic_account_manager_id.analytic_account_ids.ids,
            customer_ids=context_id.fal_analytic_account_manager_id.customer_ids.ids,
            business_unit_ids=context_id.fal_analytic_account_manager_id.business_unit_ids.ids,
            context=context_id
        ).get_lines(self, context_id, currency_table, linesDicts)
        res += line_obj_cfs.with_context(
            state=context_id.all_entries and 'all' or 'posted',
            cash_basis=self.report_type == 'date_range_cash' or context_id.cash_basis,
            strict_range=self.report_type == 'date_range_extended',
            aged_balance=self.report_type == 'date_range_extended',
            company_ids=context_id.company_ids.ids,
            context=context_id
        ).get_lines(self, context_id, currency_table, linesDicts)
        return res


class report_account_general_ledger(models.AbstractModel):
    _inherit = "account.general.ledger"

    @api.model
    def get_lines(self, context_id, line_id=None):
        if type(context_id) == int:
            context_id = self.env['account.context.general.ledger'].search([['id', '=', context_id]])
        new_context = dict(self.env.context)
        new_context.update({
            'date_from': context_id.date_from,
            'date_to': context_id.date_to,
            'state': context_id.all_entries and 'all' or 'posted',
            'cash_basis': context_id.cash_basis,
            'context_id': context_id,
            'company_ids': context_id.company_ids.ids,
            'account_analytic_ids': context_id.fal_analytic_account_manager_id.analytic_account_ids.ids,
            'customer_ids': context_id.fal_analytic_account_manager_id.customer_ids.ids,
            'business_unit_ids': context_id.fal_analytic_account_manager_id.business_unit_ids.ids,
        })
        return self.with_context(new_context)._lines(line_id)


class account_context_general_ledger(models.TransientModel):
    _inherit = "account.context.general.ledger"
    _inherits = {'fal.account.report.analytic.account.manager': 'fal_analytic_account_manager_id'}

    @api.multi
    def get_html_and_data(self, given_context=None):
        result = super(account_context_general_ledger, self).get_html_and_data(given_context=given_context)
        result['analytic_account_ids'] = [[at.id, at.name] for at in self.fal_analytic_account_manager_id.analytic_account_ids]
        result['available_analytic_account_ids'] = self.fal_analytic_account_manager_id.get_available_analytic_account_ids_and_names()
        result['customer_ids'] = [[at.id, at.name] for at in self.fal_analytic_account_manager_id.customer_ids]
        result['available_customer_ids'] = self.fal_analytic_account_manager_id.get_available_customer_ids_and_names()
        result['business_unit_ids'] = [[at.id, at.name] for at in self.fal_analytic_account_manager_id.business_unit_ids]
        result['available_business_unit_ids'] = self.fal_analytic_account_manager_id.get_available_business_unit_ids_and_names()
        result['report_context']['analytic_account_ids'] = result['analytic_account_ids']
        result['report_context']['available_analytic_account_ids'] = result['available_analytic_account_ids']
        result['report_context']['customer_ids'] = result['customer_ids']
        result['report_context']['available_customer_ids'] = result['available_customer_ids']
        result['report_context']['business_unit_ids'] = result['business_unit_ids']
        result['report_context']['available_business_unit_ids'] = result['available_business_unit_ids']

        return result

account_context_general_ledger()
