/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onMounted } from "@odoo/owl";

/**
 * Login Alert Service - checks for unseen task alerts on page load
 * and shows Odoo notification banners.
 */
class LoginAlertService extends Component {
    static template = "task_project_management.LoginAlertService";

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.action = useService("action");
        this._checked = false;

        onMounted(async () => {
            if (!this._checked) {
                this._checked = true;
                await this.checkAlerts();
            }
        });
    }

    async checkAlerts() {
        try {
            const result = await this.orm.call(
                "task.management.task", "get_login_alerts", []
            );

            // Member alerts: new task assignments
            if (result.member_alerts && result.member_alerts.length) {
                const count = result.member_alerts.length;
                const names = result.member_alerts
                    .map(a => a.assignment_name || a.project_name)
                    .slice(0, 3)
                    .join(", ");
                const suffix = count > 3 ? ` (+${count - 3} more)` : "";

                this.notification.add(
                    `You have ${count} new task assignment(s): ${names}${suffix}`,
                    {
                        type: "info",
                        title: "New Assignments",
                        sticky: true,
                        buttons: [
                            {
                                name: "View Assignments",
                                onClick: async () => {
                                    await this.orm.call(
                                        "task.management.task",
                                        "acknowledge_member_alerts",
                                        []
                                    );
                                    this.action.doAction("task_project_management.action_my_assignments");
                                },
                                primary: true,
                            },
                            {
                                name: "Dismiss",
                                onClick: async () => {
                                    await this.orm.call(
                                        "task.management.task",
                                        "acknowledge_member_alerts",
                                        []
                                    );
                                },
                            },
                        ],
                    }
                );
            }

            // PM alerts: new task submissions to review
            if (result.pm_alerts && result.pm_alerts.length) {
                const count = result.pm_alerts.length;
                const names = result.pm_alerts
                    .map(a => `${a.member_name} (${a.project_name})`)
                    .slice(0, 3)
                    .join(", ");
                const suffix = count > 3 ? ` (+${count - 3} more)` : "";

                this.notification.add(
                    `${count} new task submission(s) to review: ${names}${suffix}`,
                    {
                        type: "warning",
                        title: "Tasks Pending Review",
                        sticky: true,
                        buttons: [
                            {
                                name: "Review Tasks",
                                onClick: async () => {
                                    await this.orm.call(
                                        "task.management.task",
                                        "acknowledge_pm_alerts",
                                        []
                                    );
                                    this.action.doAction("task_project_management.action_tasks_to_review");
                                },
                                primary: true,
                            },
                            {
                                name: "Dismiss",
                                onClick: async () => {
                                    await this.orm.call(
                                        "task.management.task",
                                        "acknowledge_pm_alerts",
                                        []
                                    );
                                },
                            },
                        ],
                    }
                );
            }
        } catch (e) {
            // Silently fail - don't block user with alert errors
            console.warn("Login alert check failed:", e);
        }
    }
}

// Register as a systray component that runs on load
registry.category("systray").add(
    "task_project_management.LoginAlertService",
    { Component: LoginAlertService, props: {} },
    { sequence: 1000 }
);
