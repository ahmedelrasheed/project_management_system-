from odoo import models, fields, api, _
from odoo.exceptions import AccessError


class TaskManagementArchive(models.Model):
    _name = 'task.management.archive'
    _description = 'Shared Library'
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
        """Check that the current user is the owner of this library entry."""
        is_admin = self.env.user.has_group(
            'task_project_management.group_admin_manager')
        for rec in self:
            if not is_admin and rec.user_id.id != self.env.uid:
                raise AccessError(
                    _('You can only modify your own library entries.'))

    def _sync_attachment_visibility(self):
        """Set attachment public flag based on library visibility."""
        for rec in self:
            if rec.attachment_ids:
                rec.attachment_ids.sudo().write({
                    'public': rec.visibility == 'public',
                })

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._sync_attachment_visibility()
        return records

    def write(self, vals):
        self._check_owner()
        result = super().write(vals)
        if 'visibility' in vals or 'attachment_ids' in vals:
            self._sync_attachment_visibility()
        return result

    def unlink(self):
        self._check_owner()
        return super().unlink()
