from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class TaskManagementMember(models.Model):
    _name = 'task.management.member'
    _description = 'Organization Member'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string='Name', required=True, tracking=True)
    email = fields.Char(string='Email', required=True, tracking=True)
    phone = fields.Char(string='Phone')
    job_title = fields.Char(string='Job Title')
    address = fields.Text(string='Address')
    user_id = fields.Many2one(
        'res.users', string='Related User',
        ondelete='restrict', tracking=True,
    )

    # Relational fields
    managed_project_ids = fields.Many2many(
        'task.management.project',
        'project_manager_rel',
        'member_id', 'project_id',
        string='Managed Projects',
    )
    member_project_ids = fields.Many2many(
        'task.management.project',
        'project_member_rel',
        'member_id', 'project_id',
        string='Member Projects',
    )
    task_ids = fields.One2many(
        'task.management.task', 'member_id',
        string='Tasks',
    )
    archive_ids = fields.One2many(
        'task.management.archive', 'member_id',
        string='Archive Entries',
    )

    _sql_constraints = [
        ('email_unique', 'UNIQUE(email)',
         'A member with this email already exists.'),
        ('user_id_unique', 'UNIQUE(user_id)',
         'This user is already linked to another member.'),
    ]

    @api.model
    def _get_member_for_user(self, user=None):
        """Get the member record for a given user (or current user)."""
        if user is None:
            user = self.env.user
        return self.search([('user_id', '=', user.id)], limit=1)
