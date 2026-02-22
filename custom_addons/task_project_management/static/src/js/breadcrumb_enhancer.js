/** @odoo-module **/

import { ControlPanel } from "@web/search/control_panel/control_panel";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { onMounted, onPatched } from "@odoo/owl";

// Models that are report wizards — hide breadcrumb entirely
const REPORT_WIZARD_MODELS = [
    'task.management.member.performance.report',
    'task.management.project.performance.report',
];

patch(ControlPanel.prototype, {
    setup() {
        super.setup(...arguments);
        try {
            this.menuService = useService("menu");
        } catch (_e) {
            this.menuService = null;
        }
        onMounted(() => this._enhanceBreadcrumb());
        onPatched(() => this._enhanceBreadcrumb());
    },

    _enhanceBreadcrumb() {
        if (!this.menuService) return;

        requestAnimationFrame(() => {
            const cpEl = document.querySelector('.o_action_manager .o_control_panel');
            if (!cpEl) return;

            const breadcrumbOl = cpEl.querySelector('.breadcrumb');
            if (!breadcrumbOl) return;

            // Check if this is a report wizard — hide breadcrumb entirely
            const resModel = this.env?.config?.resModel || '';
            if (REPORT_WIZARD_MODELS.includes(resModel)) {
                breadcrumbOl.style.display = 'none';
                return;
            }

            // Otherwise show breadcrumb and inject section name
            breadcrumbOl.style.display = '';

            // Remove previously injected section to avoid duplicates
            const existing = breadcrumbOl.querySelector('.o_breadcrumb_section');
            if (existing) existing.remove();

            const sectionName = this._getMenuSectionName();
            if (!sectionName) return;

            // Create non-clickable section breadcrumb item
            const li = document.createElement('li');
            li.className = 'breadcrumb-item o_breadcrumb_section';
            li.textContent = sectionName;
            breadcrumbOl.insertBefore(li, breadcrumbOl.firstChild);
        });
    },

    _getMenuSectionName() {
        if (!this.menuService) return null;

        const currentApp = this.menuService.getCurrentApp();
        if (!currentApp || !currentApp.childrenTree) return null;

        // Read menu_id from the URL hash
        const hash = window.location.hash;
        const match = hash.match(/menu_id=(\d+)/);
        if (!match) return null;
        const menuId = parseInt(match[1]);

        // Walk the menu tree: sections are direct children of the app
        for (const section of currentApp.childrenTree) {
            if (section.id === menuId) {
                return section.name;
            }
            if (section.childrenTree) {
                for (const child of section.childrenTree) {
                    if (child.id === menuId) {
                        return section.name;
                    }
                }
            }
        }
        return null;
    },
});
