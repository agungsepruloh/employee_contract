from odoo import api, models, fields, _


class HrContract(models.Model):
    _inherit = 'hr.contract'

    @api.model
    def _cron_employee_contract_reminder(self):
        contract_reminder_days = self.env['ir.config_parameter'].sudo().get_param('employee_contract_reminder.contract_reminder_days')
        if not contract_reminder_days:
            return False
        result = []
        contract_ids = self.search([('state', '=', 'open'), ('date_end', '!=', False)])
        for contract in contract_ids:
            date_end = fields.Date.from_string(contract.date_end)
            today = fields.Date.from_string(fields.Date.today())
            if (date_end - today).days <= int(contract_reminder_days) and contract.employee_id.work_email:
                contract.send_mail_reminder()
                result.append(contract)
        return result

    def send_mail_reminder(self):
        """
        Send email to employee
        :return:
        """
        template = self.env.ref('employee_contract_reminder.email_template_employee_contract_reminder')
        template.send_mail(self.id, force_send=True, email_values={'email_to': self.employee_id.work_email})
