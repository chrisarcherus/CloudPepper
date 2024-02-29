odoo.define('bluemax_product_sales_report.product_sale', function (require) {
    'use strict';
    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var field_utils = require('web.field_utils');
    var rpc = require('web.rpc');
    var session = require('web.session');
    var utils = require('web.utils');
    var QWeb = core.qweb;
    var framework = require('web.framework');
    var _t = core._t;

    var datepicker = require('web.datepicker');
    var time = require('web.time');

    window.click_num = 0;
    var ProductSales = AbstractAction.extend({
    template: 'SaleReportTemp',
        events: {
            'click .parent-line': 'journal_line_click',
            'click .child_col1': 'journal_line_click',
            'click #apply_filter': 'apply_filter',
            'click #pdf': 'print_pdf',
            'click #xlsx': 'print_xlsx',
            'click .gl-line': 'show_drop_down',
            'click .view-account-move': 'view_acc_move',
            'mousedown div.input-group.date[data-target-input="nearest"]': '_onCalendarIconClick',

        },

        init: function(parent, action) {
        this._super(parent, action);
                this.currency=action.currency;
                this.product_report_lines = action.product_report_lines;
                this.wizard_id = action.context.wizard | null;

            },


          start: function() {
            var self = this;
            self.initial_render = true;
            rpc.query({
                model: 'account.product.sales',
                method: 'create',
                args: [{

                }]
            }).then(function(t_res) {
                self.wizard_id = t_res;

                self.load_data(self.initial_render);
            })
        },

        _onCalendarIconClick: function (ev) {
        var $calendarInputGroup = $(ev.currentTarget);

        var calendarOptions = {

        minDate: moment({ y: 1000 }),
            maxDate: moment().add(200, 'y'),
            calendarWeeks: true,
            defaultDate: moment().format(),
            sideBySide: true,
            buttons: {
                showClear: true,
                showClose: true,
                showToday: true,
            },

            icons : {
                date: 'fa fa-calendar',

            },
            locale : moment.locale(),
            format : time.getLangDateFormat(),
             widgetParent: 'body',
             allowInputToggle: true,
        };

        $calendarInputGroup.datetimepicker(calendarOptions);
    },



        load_data: function (initial_render = true) {

            var self = this;
            console.log('self.....', self);

                self.$(".categ").empty();''
                try{
                    var self = this;
                    self._rpc({
                        model: 'account.product.sales',
                        method: 'view_report',
                        args: [[this.wizard_id]],
                    }).then(function(datas) {
                    _.each(datas['product_report_lines'][0], function(rep_lines) {
                            rep_lines['direction_amount'] = self.format_currency(datas['currency'],rep_lines['direction_amount']);
                            rep_lines['direction_cost'] = self.format_currency(datas['currency'],rep_lines['direction_cost']);
                             });

                             if (initial_render) {
                            self.$('.filter_view_tb').html(QWeb.render('SalesReportFilterView', {
                                filter_data: datas['filters'],
                            }));

                            self.$el.find('.products').select2({
                            placeholder: 'Internal Reference...',
                            });
                            }


                            var child=[];

                        self.$('.table_view_tb').html(QWeb.render('InventorySaleTable', {
                                            product_report_lines : datas['product_report_lines'],
                                            filter : datas['filters'],
                                            move_lines :datas['product_report_lines'][2],
                                            currency : datas['currency'],
                                            all_total : datas['total'],
                                        }));

                });

                    }
                catch (el) {
                    window.location.href
                    }
            },
            format_currency: function(currency, amount) {
                if (typeof(amount) != 'number') {
                    amount = parseFloat(amount);
                }
                var formatted_value = (parseInt(amount)).toLocaleString(currency[2],{
                    minimumFractionDigits: 2
                })
                return formatted_value
            },


        print_pdf: function(e) {
            e.preventDefault();
            var self = this;
            self._rpc({
                model: 'account.product.sales',
                method: 'view_report',
                args: [
                    [self.wizard_id]
                ],
            }).then(function(data) {
                var action = {
                    'type': 'ir.actions.report',
                    'report_type': 'qweb-pdf',
                    'report_name': 'bluemax_product_sales_report.product_sales',
                    'report_file': 'bluemax_product_sales_report.product_sales',
                    'data': {
                        'report_data': data
                    },
                    'context': {
                        'active_model': 'account.product.sales',
                        'landscape': 1,
                        'product_sales_pdf_report': true
                    },
                    'display_name': 'Product Sales',
                };
                return self.do_action(action);
            });
        },

        print_xlsx: function() {
            var self = this;
            self._rpc({
                model: 'account.product.sales',
                method: 'view_report',
                args: [
                    [self.wizard_id]
                ],
            }).then(function(data) {
                var action = {
//                    'type': 'ir_actions_dynamic_xlsx_download',
                    'data': {
                         'model': 'account.product.sales',
                         'options': JSON.stringify(data['filters']),
                         'output_format': 'xlsx',
                         'report_data': JSON.stringify(data['product_report_lines']),
                         'report_name': 'Sales Inventory',
                         'dfr_data': JSON.stringify(data),
                    },
                };

                  self.downloadXlsx(action);
            });
        },

        downloadXlsx: function (action){
        framework.blockUI();
            session.get_file({
                url: '/dynamic_xlsx_sales_reports',
                data: action.data,
                complete: framework.unblockUI,
                error: (error) => this.call('crash_manager', 'rpc_error', error),
            });
        },

        create_lines_with_style: function(rec, attr, datas) {
            var temp_str = "";
            var style_name = "border-bottom: 1px solid #e6e6e6;";
            var attr_name = attr + " style="+style_name;



            temp_str += "<td  class='child_col1' "+attr_name+" >"+rec['code'] +rec['name'] +"</td>";
            if(datas.currency[1]=='after'){
            temp_str += "<td  class='child_col2' "+attr_name+" >"+rec['debit'].toFixed(2)+datas.currency[0]+"</td>";
            temp_str += "<td  class='child_col3' "+attr_name+" >"+rec['credit'].toFixed(2) +datas.currency[0]+ "</td>";

            }
            else{
            temp_str += "<td  class='child_col2' "+attr_name+" >"+datas.currency[0]+rec['debit'].toFixed(2) + "</td>";
            temp_str += "<td  class='child_col3' "+attr_name+">"+datas.currency[0]+rec['credit'].toFixed(2) + "</td>";

            }
            return temp_str;
        },


        journal_line_click: function (el){
            click_num++;
            var self = this;
            var line = $(el.target).parent().data('id');

            return self.do_action({
                type: 'ir.actions.act_window',
                    view_type: 'form',
                    view_mode: 'form',
                    res_model: 'account.move',
                    views: [
                        [false, 'form']
                    ],
                    res_id: line,
                    target: 'current',
            });

        },

        show_drop_down: function(event) {
            event.preventDefault();
            var self = this;
            var account_id = $(event.currentTarget).data('account-id');

            var product_id = $(event.currentTarget)[0].cells[0].innerText;
            var offset = 0;
            var td = $(event.currentTarget).next('tr').find('td');
            if (td.length == 1) {

                    self._rpc({
                        model: 'account.product.sales',
                        method: 'view_report',
                        args: [
                            [self.wizard_id]
                        ],
                    }).then(function(data) {


                    for (var i = 0; i < data['product_report_lines'][0].length; i++) {
                    if (account_id == data['product_report_lines'][0][i]['product_id'] ){
                    $(event.currentTarget).next('tr').find('td .gl-table-div').remove();
                    $(event.currentTarget).next('tr').find('td ul').after(
                        QWeb.render('SubSectionalInvoice', {
                            account_data: data['product_report_lines'][0][i]['child_lines'],
                        }))
                    $(event.currentTarget).next('tr').find('td ul li:first a').css({
                        'background-color': '#00ede8',
                        'font-weight': 'bold',
                    });
                     }
                    }

                    });


            }
        },

        view_acc_move: function(event) {
            event.preventDefault();
            var self = this;
            var context = {};
            var show_acc_move = function(res_model, res_id, view_id) {
                var action = {
                    type: 'ir.actions.act_window',
                    view_type: 'form',
                    view_mode: 'form',
                    res_model: res_model,
                    views: [
                        [view_id || false, 'form']
                    ],
                    res_id: res_id,
                    target: 'current',
                    context: context,
                };
                return self.do_action(action);
            };
            rpc.query({
                    model: 'account.move',
                    method: 'search_read',
                    domain: [
                        ['id', '=', $(event.currentTarget).data('move-id')]
                    ],
                    fields: ['id'],
                    limit: 1,
                })
                .then(function(record) {
                    if (record.length > 0) {
                        show_acc_move('account.move', record[0].id);
                    } else {
                        show_acc_move('account.move', $(event.currentTarget).data('move-id'));
                    }
                });
        },

        apply_filter: function(event) {
            event.preventDefault();
            var self = this;
            self.initial_render = false;
            var filter_data_selected = {};





            var product_ids = [];
            var product_text = [];
            var span_res = document.getElementById("products_res")
            var product_list = $(".products").select2('data')
            for (var i = 0; i < product_list.length; i++) {
            if(product_list[i].element[0].selected === true)
            {product_ids.push(parseInt(product_list[i].id))
            if(product_text.includes(product_list[i].text) === false)
            {product_text.push(product_list[i].text)
            }
            span_res.value = product_text
            span_res.innerHTML=span_res.value;
            }
            }
            if (product_list.length == 0){
            span_res.value = ""
            span_res.innerHTML="";
            }
            filter_data_selected.product_ids = product_ids


            if (this.$el.find('.datetimepicker-input[name="date_from"]').val()) {
                filter_data_selected.date_from = moment(this.$el.find('.datetimepicker-input[name="date_from"]').val(), time.getLangDateFormat()).locale('en').format('YYYY-MM-DD');
            }

            if (this.$el.find('.datetimepicker-input[name="date_to"]').val()) {
                filter_data_selected.date_to = moment(this.$el.find('.datetimepicker-input[name="date_to"]').val(), time.getLangDateFormat()).locale('en').format('YYYY-MM-DD');
            }


            rpc.query({
                model: 'account.product.sales',
                method: 'write',
                args: [
                    self.wizard_id, filter_data_selected
                ],
            }).then(function(res) {
            self.initial_render = true;
            self.load_data(self.initial_render);
            });
        },

    });
    core.action_registry.add("p_s", ProductSales);
    return ProductSales;
});