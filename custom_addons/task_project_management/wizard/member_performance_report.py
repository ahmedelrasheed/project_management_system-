import base64
import csv
import io

from odoo import models, fields, api, _
from datetime import timedelta


class MemberPerformanceReport(models.TransientModel):
    _name = 'task.management.member.performance.report'
    _description = 'Member Performance Report'

    member_id = fields.Many2one(
        'task.management.member', string='Member', required=True,
    )
    period = fields.Selection([
        ('today', 'Today'),
        ('week', 'This Week'),
        ('month', 'This Month'),
        ('custom', 'Custom Range'),
    ], string='Period', default='month', required=True)
    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')

    # Computed stats
    total_tasks = fields.Integer(
        string='Total Tasks', compute='_compute_stats')
    approved_tasks = fields.Integer(
        string='Approved Tasks', compute='_compute_stats')
    rejected_tasks = fields.Integer(
        string='Rejected Tasks', compute='_compute_stats')
    pending_tasks = fields.Integer(
        string='Pending Tasks', compute='_compute_stats')
    total_hours = fields.Float(
        string='Total Hours', compute='_compute_stats')
    approved_hours = fields.Float(
        string='Approved Hours', compute='_compute_stats')
    approval_rate = fields.Float(
        string='Approval Rate (%)', compute='_compute_stats')
    late_entries = fields.Integer(
        string='Late Entries', compute='_compute_stats')
    avg_hours_per_day = fields.Float(
        string='Avg Hours/Day', compute='_compute_stats')
    project_count = fields.Integer(
        string='Projects Worked On', compute='_compute_stats')

    # Task detail lines
    task_line_ids = fields.One2many(
        'task.management.member.performance.line', 'report_id',
        string='Task Details', compute='_compute_stats')

    # Project breakdown lines
    project_line_ids = fields.One2many(
        'task.management.member.performance.project', 'report_id',
        string='Project Breakdown', compute='_compute_stats')

    # Export fields
    report_file = fields.Binary(string='Report File', readonly=True)
    report_filename = fields.Char(string='Filename')

    def _get_date_range(self):
        """Return (date_from, date_to) based on selected period."""
        today = fields.Date.context_today(self)
        if self.period == 'today':
            return today, today
        elif self.period == 'week':
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)
            return week_start, week_end
        elif self.period == 'month':
            month_start = today.replace(day=1)
            # Last day of month
            if today.month == 12:
                month_end = today.replace(day=31)
            else:
                month_end = today.replace(
                    month=today.month + 1, day=1) - timedelta(days=1)
            return month_start, month_end
        else:
            return self.date_from or today, self.date_to or today

    @api.depends('member_id', 'period', 'date_from', 'date_to')
    def _compute_stats(self):
        TaskLine = self.env['task.management.member.performance.line']
        ProjectLine = self.env['task.management.member.performance.project']
        for report in self:
            if not report.member_id:
                report.total_tasks = 0
                report.approved_tasks = 0
                report.rejected_tasks = 0
                report.pending_tasks = 0
                report.total_hours = 0.0
                report.approved_hours = 0.0
                report.approval_rate = 0.0
                report.late_entries = 0
                report.avg_hours_per_day = 0.0
                report.project_count = 0
                report.task_line_ids = TaskLine
                report.project_line_ids = ProjectLine
                continue

            d_from, d_to = report._get_date_range()
            tasks = self.env['task.management.task'].sudo().search([
                ('member_id', '=', report.member_id.id),
                ('date', '>=', d_from),
                ('date', '<=', d_to),
            ], order='date desc, id desc')

            approved = tasks.filtered(
                lambda t: t.approval_status == 'approved')
            rejected = tasks.filtered(
                lambda t: t.approval_status == 'rejected')
            pending = tasks.filtered(
                lambda t: t.approval_status == 'pending')
            late = tasks.filtered(lambda t: t.is_late_entry)

            total = len(tasks)
            report.total_tasks = total
            report.approved_tasks = len(approved)
            report.rejected_tasks = len(rejected)
            report.pending_tasks = len(pending)
            report.total_hours = sum(tasks.mapped('duration_hours'))
            report.approved_hours = sum(approved.mapped('duration_hours'))
            report.approval_rate = round(
                (len(approved) / total * 100) if total else 0, 1)
            report.late_entries = len(late)

            # Avg hours per day (unique working days)
            unique_days = len(set(tasks.mapped('date')))
            report.avg_hours_per_day = round(
                report.total_hours / unique_days if unique_days else 0, 2)

            # Projects worked on
            projects = tasks.mapped('project_id')
            report.project_count = len(projects)

            # Task detail lines (virtual records)
            task_lines = []
            for task in tasks:
                task_lines.append((0, 0, {
                    'date': task.date,
                    'project_name': task.project_id.name,
                    'description': (task.description or '')[:80],
                    'time_from': task.time_from,
                    'time_to': task.time_to,
                    'duration_hours': task.duration_hours,
                    'approval_status': task.approval_status,
                    'is_late_entry': task.is_late_entry,
                }))
            report.task_line_ids = task_lines

            # Project breakdown lines
            project_lines = []
            for proj in projects:
                p_tasks = tasks.filtered(
                    lambda t, p=proj: t.project_id == p)
                p_approved = p_tasks.filtered(
                    lambda t: t.approval_status == 'approved')
                p_total = len(p_tasks)
                project_lines.append((0, 0, {
                    'project_name': proj.name,
                    'task_count': p_total,
                    'total_hours': sum(
                        p_tasks.mapped('duration_hours')),
                    'approved_hours': sum(
                        p_approved.mapped('duration_hours')),
                    'approval_rate': round(
                        (len(p_approved) / p_total * 100)
                        if p_total else 0, 1),
                    'late_entries': len(
                        p_tasks.filtered(lambda t: t.is_late_entry)),
                }))
            report.project_line_ids = project_lines


    def action_export_csv(self):
        """Export the performance report as CSV."""
        self.ensure_one()
        if not self.member_id:
            return
        d_from, d_to = self._get_date_range()
        tasks = self.env['task.management.task'].sudo().search([
            ('member_id', '=', self.member_id.id),
            ('date', '>=', d_from),
            ('date', '<=', d_to),
        ], order='date desc, id desc')

        output = io.StringIO()
        writer = csv.writer(output)

        # Summary header
        writer.writerow(['Member Performance Report'])
        writer.writerow(['Member', self.member_id.name])
        writer.writerow(['Period', f'{d_from} to {d_to}'])
        writer.writerow([])

        # KPI summary
        writer.writerow(['--- Performance Summary ---'])
        writer.writerow(['Total Tasks', self.total_tasks])
        writer.writerow(['Approved', self.approved_tasks])
        writer.writerow(['Rejected', self.rejected_tasks])
        writer.writerow(['Pending', self.pending_tasks])
        writer.writerow(['Total Hours', f'{self.total_hours:.2f}'])
        writer.writerow(['Approved Hours', f'{self.approved_hours:.2f}'])
        writer.writerow(['Approval Rate', f'{self.approval_rate:.1f}%'])
        writer.writerow(['Late Entries', self.late_entries])
        writer.writerow(['Avg Hours/Day', f'{self.avg_hours_per_day:.2f}'])
        writer.writerow(['Projects Worked On', self.project_count])
        writer.writerow([])

        # Project breakdown
        writer.writerow(['--- Project Breakdown ---'])
        writer.writerow([
            'Project', 'Tasks', 'Total Hours', 'Approved Hours',
            'Approval Rate', 'Late Entries',
        ])
        projects = tasks.mapped('project_id')
        for proj in projects:
            p_tasks = tasks.filtered(lambda t, p=proj: t.project_id == p)
            p_approved = p_tasks.filtered(
                lambda t: t.approval_status == 'approved')
            p_total = len(p_tasks)
            writer.writerow([
                proj.name,
                p_total,
                f'{sum(p_tasks.mapped("duration_hours")):.2f}',
                f'{sum(p_approved.mapped("duration_hours")):.2f}',
                f'{round((len(p_approved) / p_total * 100) if p_total else 0, 1)}%',
                len(p_tasks.filtered(lambda t: t.is_late_entry)),
            ])
        writer.writerow([])

        # Task details
        writer.writerow(['--- Task Details ---'])
        writer.writerow([
            'Date', 'Project', 'Description', 'From', 'To',
            'Hours', 'Status', 'Late Entry',
        ])
        for task in tasks:
            writer.writerow([
                str(task.date),
                task.project_id.name,
                (task.description or '')[:80],
                self._float_to_time(task.time_from),
                self._float_to_time(task.time_to),
                f'{task.duration_hours:.2f}',
                task.approval_status,
                'Yes' if task.is_late_entry else 'No',
            ])

        csv_data = output.getvalue().encode('utf-8-sig')
        self.report_file = base64.b64encode(csv_data)
        member_name = self.member_id.name.replace(' ', '_')
        self.report_filename = (
            f'performance_{member_name}_{d_from}_{d_to}.csv')
        return {
            'type': 'ir.actions.act_url',
            'url': (
                f'/web/content?model={self._name}'
                f'&id={self.id}'
                f'&field=report_file'
                f'&filename_field=report_filename'
                f'&download=true'
            ),
            'target': 'new',
        }

    @staticmethod
    def _float_to_time(value):
        hours = int(value)
        minutes = int((value - hours) * 60)
        return f'{hours:02d}:{minutes:02d}'


class MemberPerformanceLine(models.TransientModel):
    _name = 'task.management.member.performance.line'
    _description = 'Member Performance Report - Task Line'

    report_id = fields.Many2one(
        'task.management.member.performance.report',
        string='Report')
    date = fields.Date(string='Date')
    project_name = fields.Char(string='Project')
    description = fields.Char(string='Description')
    time_from = fields.Float(string='From')
    time_to = fields.Float(string='To')
    duration_hours = fields.Float(string='Hours')
    approval_status = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Status')
    is_late_entry = fields.Boolean(string='Late')


class MemberPerformanceProject(models.TransientModel):
    _name = 'task.management.member.performance.project'
    _description = 'Member Performance Report - Project Line'

    report_id = fields.Many2one(
        'task.management.member.performance.report',
        string='Report')
    project_name = fields.Char(string='Project')
    task_count = fields.Integer(string='Tasks')
    total_hours = fields.Float(string='Total Hours')
    approved_hours = fields.Float(string='Approved Hours')
    approval_rate = fields.Float(string='Approval Rate (%)')
    late_entries = fields.Integer(string='Late Entries')
