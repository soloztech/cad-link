/** @odoo-module **/
// SPDX-License-Identifier: LGPL-3.0-or-later
import { Component, onWillUnmount, useEffect, useState } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";

export class CadDocuments extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        this.state = useState({ loading: true, error: "", data: null });
        this.sequence = 0;
        // Notebook mounts only its active page: opening another product tab
        // does not read SMB. Discard stale replies when navigating or editing.
        useEffect(
            () => { this.load(); },
            () => [this.props.record.resModel, this.props.record.resId, this.props.record.isDirty]
        );
        onWillUnmount(() => { this.sequence++; });
    }

    get needsSave() {
        return !this.props.record.resId || this.props.record.isDirty;
    }

    async load() {
        const sequence = ++this.sequence;
        this.state.data = null;
        this.state.error = "";
        this.state.loading = !this.needsSave;
        if (this.needsSave) {
            return;
        }
        const record = this.props.record;
        try {
            const data = await this.orm.call(record.resModel, "get_cad_documents", [[record.resId]], {
                context: record.context,
            });
            if (sequence === this.sequence) {
                this.state.data = data;
            }
        } catch (error) {
            if (sequence === this.sequence) {
                this.state.error = error.data?.message || _t("CAD documents could not be loaded.");
            }
        } finally {
            if (sequence === this.sequence) {
                this.state.loading = false;
            }
        }
    }

    async selectVariant() {
        const record = this.props.record;
        const action = await this.orm.call(record.resModel, "action_open_cad_documents", [[record.resId]], {
            context: record.context,
        });
        await this.action.doAction(action);
    }

    async copyFolder() {
        try {
            await navigator.clipboard.writeText(this.state.data.folder_path);
            this.notification.add(_t("Folder path copied."), { type: "success" });
        } catch {
            this.notification.add(_t("Select and copy the folder path shown above."), { type: "info" });
        }
    }

    formatSize(size) {
        if (size >= 1024 * 1024) {
            return (size / (1024 * 1024)).toFixed(1) + " MiB";
        }
        return Math.ceil(size / 1024) + " KiB";
    }
}

CadDocuments.template = "cad_link.CadDocuments";
CadDocuments.props = { ...standardWidgetProps };
registry.category("view_widgets").add("cad_documents", CadDocuments);
