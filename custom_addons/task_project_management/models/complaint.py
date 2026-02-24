from odoo import models, fields, api, _
from odoo.exceptions import UserError
from markupsafe import Markup


class TaskManagementComplaint(models.Model):
    _name = 'task.management.complaint'
    _description = 'Task Complaint'
    _inherit = ['mail.thread']
    _order = 'create_date desc'

    task_id = fields.Many2one(
        'task.management.task', string='Task',
        required=True, ondelete='cascade', readonly=True,
    )
    member_id = fields.Many2one(
        'task.management.member', string='Filed By',
        required=True, readonly=True,
    )
    message = fields.Text(string='Complaint Message', required=True)
    status = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Status', default='pending', required=True, tracking=True)
    manager_comment = fields.Text(string='Manager Comment')
    reviewed_by = fields.Many2one(
        'res.users', string='Reviewed By', readonly=True,
    )
    reviewed_date = fields.Datetime(string='Reviewed Date', readonly=True)
    project_id = fields.Many2one(
        related='task_id.project_id', string='Project',
        store=True, readonly=True,
    )
    task_approval_status = fields.Selection(
        related='task_id.approval_status', string='Task Status',
        readonly=True,
    )

    _sql_constraints = [
        ('task_unique', 'UNIQUE(task_id)',
         'Only one complaint can be filed per task.'),
    ]

    def action_approve(self):
        for complaint in self:
            if complaint.status != 'pending':
                raise UserError(_('Only pending complaints can be approved.'))
            complaint.write({
                'status': 'approved',
                'reviewed_by': self.env.uid,
                'reviewed_date': fields.Datetime.now(),
            })
            # Change task status to approved
            task = complaint.task_id
            task.sudo().write({
                'approval_status': 'approved',
                'manager_comment': _(
                    'Approved via complaint review by %s'
                ) % self.env.user.name,
            })
            # Notify member
            self._notify_member(
                complaint,
                _('Your complaint for task "%s" has been approved. '
                  'The task has been marked as approved.') % (
                    task.description or task.assignment_name or ''),
            )

    def action_reject(self):
        for complaint in self:
            if complaint.status != 'pending':
                raise UserError(_('Only pending complaints can be rejected.'))
            complaint.write({
                'status': 'rejected',
                'reviewed_by': self.env.uid,
                'reviewed_date': fields.Datetime.now(),
            })
            # Notify member (no task change)
            task = complaint.task_id
            self._notify_member(
                complaint,
                _('Your complaint for task "%s" has been rejected.') % (
                    task.description or task.assignment_name or ''),
            )

    def _notify_member(self, complaint, message_text):
        try:
            member_partner = complaint.member_id.user_id.partner_id
            if member_partner:
                body = Markup('<p>%s</p>') % message_text
                if complaint.manager_comment:
                    body += Markup(
                        '<p>Manager comment: %s</p>'
                    ) % complaint.manager_comment
                complaint.sudo().message_post(
                    body=body,
                    partner_ids=[member_partner.id],
                    message_type='notification',
                    subtype_xmlid='mail.mt_note',
                )
        except Exception:
            pass
