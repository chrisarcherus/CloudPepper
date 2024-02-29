/** @odoo-module */

import {ListRenderer} from "@web/views/list/list_renderer";
import {Component} from "@odoo/owl";
import {useService} from "@web/core/utils/hooks";

export class TreeMany2oneClickableButton extends Component {
    setup() {
        this.actionService = useService("action");
    }

    async onClick(ev) {
        ev.stopPropagation();
        return this.actionService.doAction({
            type: "ir.actions.act_window",
            res_model: this.props.field.relation,
            res_id: this.props.value[0],
            views: [[false, "form"]],
            target: "target",
            additionalContext: this.props.context || {},
        });
    }
}
TreeMany2oneClickableButton.template = "web_tree_many2one_clickable.Button";

Object.assign(ListRenderer.components, {TreeMany2oneClickableButton});
