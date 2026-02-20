from odoo import models, fields, api, _
from odoo.exceptions import AccessError


class TaskManagementArchive(models.Model):
    _name = 'task.management.archive'
    _description = 'Member Project Archive / Portfolio'
    _order = 'end_date desc, id desc'

    member_id = fields.Many2one(
        'task.management.member', string='Member',
        required=False, ondelete='set null', index=True,
        default=lambda self: self.env['task.management.member']._get_member_for_user(),
    )
    user_id = fields.Many2one(
        'res.users', string='User', required=True,
        default=lambda self: self.env.uid, index=True,
    )
    project_name = fields.Char(string='Project Name', required=True)
    description = fields.Text(string='Description')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    role_played = fields.Char(string='Role Played')
    visibility = fields.Selection([
        ('public', 'Public'),
        ('private', 'Private'),
    ], string='Visibility', default='private', required=True)
    attachment_ids = fields.Many2many(
        'ir.attachment', 'archive_attachment_rel',
        'archive_id', 'attachment_id',
        string='Attachments',
    )

    def _check_owner(self):
        """Check that the current user is the owner of this archive entry."""
        is_admin = self.env.user.has_group(
            'task_project_management.group_admin_manager')
        for rec in self:
            if not is_admin and rec.user_id.id != self.env.uid:
                raise AccessError(
                    _('You can only modify your own archive entries.'))

    def write(self, vals):
        self._check_owner()
        return super().write(vals)

    def unlink(self):
        self._check_owner()
        return super().unlink()
