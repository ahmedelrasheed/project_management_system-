from odoo import models, fields, api, _
from odoo.exceptions import UserError
from markupsafe import Markup


class TaskManagementComplaintWizard(models.TransientModel):
    _name = 'task.management.complaint.wizard'
    _description = 'File Complaint Wizard'

    task_id = fields.Many2one(
        'task.management.task', string='Task',
        required=True, readonly=True,
    )
    message = fields.Text(string='Complaint Message', required=True)

    def action_submit(self):
        self.ensure_one()
        task = self.task_id
        # Validate task is rejected
        if task.approval_status != 'rejected':
            raise UserError(
                _('You can only file a complaint for rejected tasks.'))
        # Validate no existing complaint
        existing = self.env['task.management.complaint'].search(
            [('task_id', '=', task.id)], limit=1)
        if existing:
            raise UserError(
                _('A complaint has already been filed for this task.'))
        # Get current member
        member = self.env['task.management.member'].sudo()._get_member_for_user()
        if not member or member != task.member_id:
            raise UserError(
                _('You can only file complaints for your own tasks.'))
        # Create complaint
        complaint = self.env['task.management.complaint'].create({
            'task_id': task.id,
            'member_id': member.id,
            'message': self.message,
        })
        # Notify managers of the project
        self._notify_managers(complaint)
        return {'type': 'ir.actions.act_window_close'}

    def _notify_managers(self, complaint):
        try:
            project = complaint.task_id.project_id
            manager_partners = project.sudo().manager_ids.mapped(
                'user_id.partner_id')
            if manager_partners:
                body = Markup(
                    '<p>New complaint filed by <strong>%s</strong> '
                    'for task in project <strong>%s</strong>.</p>'
                    '<p>Message: %s</p>'
                ) % (
                    complaint.member_id.name or '',
                    project.name or '',
                    complaint.message or '',
                )
                complaint.sudo().message_post(
                    body=body,
                    partner_ids=manager_partners.ids,
                    message_type='notification',
                    subtype_xmlid='mail.mt_note',
                )
        except Exception:
            pass
