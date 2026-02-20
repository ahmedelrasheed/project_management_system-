from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class TaskManagementProject(models.Model):
    _name = 'task.management.project'
    _description = 'Project'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(string='Project Name', required=True, tracking=True)
    description = fields.Text(string='Description')
    expected_hours = fields.Float(
        string='Expected Hours', required=True, tracking=True)
    expected_end_date = fields.Date(
        string='Expected End Date', tracking=True)
    status = fields.Selection([
        ('active', 'Active'),
        ('on_hold', 'On Hold'),
        ('completed', 'Completed'),
        ('archived', 'Archived'),
    ], string='Status', default='active', required=True, tracking=True)

    # Relations
    project_manager_ids = fields.Many2many(
        'task.management.member',
        'project_manager_rel',
        'project_id', 'member_id',
        string='Project Managers',
    )
    member_ids = fields.Many2many(
        'task.management.member',
        'project_member_rel',
        'project_id', 'member_id',
        string='Members',
    )
    removed_member_ids = fields.Many2many(
        'task.management.member',
        'project_removed_member_rel',
        'project_id', 'member_id',
        string='Removed Members',
    )
    task_ids = fields.One2many(
        'task.management.task', 'project_id',
        string='Tasks',
    )

    # Computed fields
    total_logged_hours = fields.Float(
        string='Total Logged Hours',
        compute='_compute_total_logged_hours',
        store=True,
    )
    progress_percentage = fields.Float(
        string='Progress (%)',
        compute='_compute_progress_percentage',
    )
    task_count = fields.Integer(
        string='Task Count',
        compute='_compute_task_stats',
    )
    pending_task_count = fields.Integer(
        string='Pending Tasks',
        compute='_compute_task_stats',
    )

    @api.depends('task_ids.duration_hours', 'task_ids.approval_status')
    def _compute_total_logged_hours(self):
        for project in self:
            approved_tasks = project.task_ids.filtered(
                lambda t: t.approval_status == 'approved')
            project.total_logged_hours = sum(
                approved_tasks.mapped('duration_hours'))

    @api.depends('total_logged_hours', 'expected_hours')
    def _compute_progress_percentage(self):
        for project in self:
            if project.expected_hours > 0:
                project.progress_percentage = min(
                    (project.total_logged_hours / project.expected_hours) * 100,
                    100.0)
            else:
                project.progress_percentage = 0.0

    @api.depends('task_ids', 'task_ids.approval_status')
    def _compute_task_stats(self):
        for project in self:
            project.task_count = len(project.task_ids)
            project.pending_task_count = len(
                project.task_ids.filtered(
                    lambda t: t.approval_status == 'pending'))

    @api.constrains('project_manager_ids', 'member_ids')
    def _check_pm_not_member(self):
        for project in self:
            overlap = project.project_manager_ids & project.member_ids
            if overlap:
                names = ', '.join(overlap.mapped('name'))
                raise ValidationError(
                    _('A Project Manager cannot also be a member of the '
                      'same project: %s') % names)

    @api.constrains('project_manager_ids')
    def _check_at_least_one_pm(self):
        for project in self:
            if not project.project_manager_ids:
                raise ValidationError(
                    _('A project must have at least one Project Manager.'))

    def write(self, vals):
        # Track removed members
        if 'member_ids' in vals:
            for project in self:
                old_members = project.member_ids
                result = super(TaskManagementProject, project).write(vals)
                new_members = project.member_ids
                removed = old_members - new_members
                if removed:
                    # Add to removed_member_ids without triggering recursion
                    existing_removed = project.removed_member_ids
                    all_removed = existing_removed | removed
                    super(TaskManagementProject, project).write({
                        'removed_member_ids': [(6, 0, all_removed.ids)],
                    })
            return True
        return super().write(vals)

    @api.model
    def _cron_check_project_deadlines(self):
        """Check for projects that have reached their expected end date
        with pending tasks. Notify PM and Admin."""
        today = fields.Date.context_today(self)
        projects = self.search([
            ('status', '=', 'active'),
            ('expected_end_date', '<=', today),
        ])
        for project in projects:
            pending_count = project.pending_task_count
            if pending_count > 0:
                # Notify PMs
                pm_partners = project.project_manager_ids.mapped(
                    'user_id.partner_id')
                # Notify admins
                admin_group = self.env.ref(
                    'task_project_management.group_admin_manager')
                admin_partners = admin_group.users.mapped('partner_id')
                all_partners = pm_partners | admin_partners
                if all_partners:
                    try:
                        project.sudo().message_post(
                            body=_(
                                'Project "%(name)s" has reached its expected '
                                'end date (%(date)s) with %(count)s pending '
                                'task(s).',
                                name=project.name,
                                date=project.expected_end_date,
                                count=pending_count,
                            ),
                            partner_ids=all_partners.ids,
                            message_type='notification',
                            subtype_xmlid='mail.mt_note',
                        )
                    except Exception:
                        pass
