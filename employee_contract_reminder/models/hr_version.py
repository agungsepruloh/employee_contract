from dateutil.relativedelta import relativedelta
from odoo import api, models, fields, _


class HrVersion(models.Model):
    _inherit = 'hr.version'

    @api.model
    def _cron_employee_contract_reminder(self):
        """
        Cron job to send email to employee
        :return:
        """
        version_ids = self.get_versions_to_remind().filtered(lambda version: version.employee_id.work_email)
        version_ids.send_mail_reminder()
        return version_ids

    @api.model
    def get_versions_to_remind(self):
        """
        Get contract versions to remind
        :return:
        """
        contract_reminder_days = self.env['ir.config_parameter'].sudo().get_param('employee_contract_reminder.contract_reminder_days')
        if not contract_reminder_days:
            return []
        version_ids = self.search([
            ('active', '=', True),
            ('contract_date_end', '!=', False),
            ('contract_date_end', '>=', fields.Date.today()),
            ('contract_date_end', '<=', fields.Date.today() + relativedelta(days=int(contract_reminder_days)))
        ])
        return version_ids

    def send_mail_reminder(self):
        """
        Send email to employee
        :return:
        """
        template = self.env.ref('employee_contract_reminder.email_template_employee_contract_reminder')
        for version in self:
            template.send_mail(version.id, force_send=True, email_values={'email_to': version.employee_id.work_email})
