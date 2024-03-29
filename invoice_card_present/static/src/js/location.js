/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { markup } from "@odoo/owl";
import { registry } from "@web/core/registry";
const widgetRegistry = registry.category("view_widgets");
import { _t } from "@web/core/l10n/translation";

publicWidget.registry.PaymentProcess = publicWidget.Widget.extend({
    template: 'LegacyAttachDocument',
    events: {
        'click': '_onClickProcessPaymentWidget',
        'change input.o_input_file': '_onFileChanged',
    },
    /**
     * @constructor
     * @param {Widget} parent
     * @param {Object} record
     * @param {Object} nodeInfo
     */
    init: function(parent, record, nodeInfo) {
        this._super.apply(this, arguments);
        this.res_id = record.res_id;
        this.res_model = record.model;
        this.state = record;
        this.node = nodeInfo;
        this.fileuploadID = _.uniqueId('o_fileupload');
    },
    /**
     * @override
     */
    start: function() {
        $(window).on(this.fileuploadID, this._onFileLoaded.bind(this));
        return this._super.apply(this, arguments);
    },
    /**
     * @override
     */
    destroy: function() {
        $(window).off(this.fileuploadID);
        this._super.apply(this, arguments);
    },

    //--------------------------------------------------------------------------
    // private
    //--------------------------------------------------------------------------

    /**
     * Helper function to display a warning that some fields have an invalid
     * value. This is used when a save operation cannot be completed.
     *
     * @private
     * @param {string[]} invalidFields - list of field names
     */
    _notifyInvalidFields: function(invalidFields) {
        var fields = this.state.fields;
        var warnings = invalidFields.map(function(fieldName) {
            var fieldStr = fields[fieldName].string;
            return _.str.sprintf('<li>%s</li>', _.escape(fieldStr));
        });
        warnings.unshift('<ul>');
        warnings.push('</ul>');
        this.displayNotification({
            title: _t("Invalid fields:"),
            message: markup(warnings.join('')),
            type: 'danger',
        });
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * Opens File Explorer dialog if all fields are valid and record is saved
     *
     * @private
     * @param {Event} ev
     */
    _onClickProcessPaymentWidget: function(ev) {
        if ($(ev.target).is('input.o_input_file')) {
            return;
        }
        var fieldNames = this.getParent().canBeSaved(this.state.id);
        if (fieldNames.length) {
            return this._notifyInvalidFields(fieldNames);
        }
        // We want to save record on widget click and then open File Selection Explorer
        // but due to this security restriction give warning to save record first.
        // https://stackoverflow.com/questions/29728705/trigger-click-on-input-file-on-asynchronous-ajax-done/29873845#29873845
        if (!this.res_id) {
            return this.displayNotification({ message: _t('Please save before attaching a file'), type: 'danger' });
        }
        this.$('input.o_input_file').trigger('click');
    },
    /**
     * Submits file
     *
     * @private
     * @param {Event} ev
     */
    _onFileChanged: function(ev) {
        ev.stopPropagation();
        this.$('form.o_form_binary_form').trigger('submit');
        this.call('ui', 'block');
    },
    /**
     * Call action given as node attribute after file submission
     *
     * @private
     */
    _onFileLoaded: function() {
        var self = this;
        // the first argument isn't a file but the jQuery.Event
        var files = Array.prototype.slice.call(arguments, 1);
        return new Promise(function(resolve) {
            if (self.node.attrs.action) {
                this.env.services.orm.silent.call(
                    self.res_model,
                    self.node.attrs.action,
                    [self.res_id], {
                        attachment_ids: _.map(files, function(file) {
                            return file.id;
                        }),
                    }
                ).then(function() {
                    resolve();
                });
            } else {
                resolve();
            }
        }).then(function() {
            self.trigger_up('reload');
            this.call('ui', 'unblock');
        });
    },

});
export default publicWidget.registry.PaymentProcess;
