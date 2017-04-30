odoo.define('fal_account_report_filter.fal_account_report_generic', function (require) {
'use strict';

var core = require('web.core');
var Account_report_generic = require('account_reports.account_report_generic');
var Model = require('web.Model');
var session = require('web.session');
var QWeb = core.qweb;

    Account_report_generic.include({
        render_searchview_buttons: function() {
            var self = this;
            this.$searchview_buttons = this._super();
            this.$searchview_buttons.find(".o_account_reports_analytic_account_auto_complete").select2();
            this.$searchview_buttons.find(".o_account_reports_customer_auto_complete").select2();
            this.$searchview_buttons.find(".o_account_reports_business_unit_auto_complete").select2();

            if (this.report_context.analytic_account_ids){
                var selection = [];
                var i;
                for (var i = 0; i < this.report_context.analytic_account_ids.length; i++) {
                    selection.push({id:this.report_context.analytic_account_ids[i][0], text:this.report_context.analytic_account_ids[i][1]});
                }
                this.$searchview_buttons.find('.o_account_reports_analytic_account_auto_complete').data().select2.updateSelection(selection);
            };
            if (this.report_context.customer_ids){
                var selection = [];
                var i;
                for (var i = 0; i < this.report_context.customer_ids.length; i++) {
                    selection.push({id:this.report_context.customer_ids[i][0], text:this.report_context.customer_ids[i][1]});
                }
                this.$searchview_buttons.find('.o_account_reports_customer_auto_complete').data().select2.updateSelection(selection);
            };
            if (this.report_context.business_unit_ids){
                var selection = [];
                var i;
                for (var i = 0; i < this.report_context.business_unit_ids.length; i++) {
                    selection.push({id:this.report_context.business_unit_ids[i][0], text:this.report_context.business_unit_ids[i][1]});
                }
                this.$searchview_buttons.find('.o_account_reports_business_unit_auto_complete').data().select2.updateSelection(selection);
            };
            this.$searchview_buttons.find('.o_account_reports_add_analytic_account').bind('click', function (event) {
                var report_context = {};
                var value = self.$searchview_buttons.find(".o_account_reports_analytic_account_auto_complete").select2("val");
                report_context.analytic_account_ids = value;
                self.restart(report_context);
            });
            this.$searchview_buttons.find('.o_account_reports_add_customer').bind('click', function (event) {
                var report_context = {};
                var value = self.$searchview_buttons.find(".o_account_reports_customer_auto_complete").select2("val");
                report_context.customer_ids = value;
                self.restart(report_context);
            });
            this.$searchview_buttons.find('.o_account_reports_add_business_unit').bind('click', function (event) {
                var report_context = {};
                var value = self.$searchview_buttons.find(".o_account_reports_business_unit_auto_complete").select2("val");
                report_context.business_unit_ids = value;
                self.restart(report_context);
            });
            return this.$searchview_buttons;
        },
        get_html: function() {
            var res = this._super.apply(this, arguments);
            if(res.report_context){
                res.report_context.analytic_account_ids = res.analytic_account_ids;
                res.report_context.customer_ids = res.customer_ids;
            }
            return res;
        },
    });

});