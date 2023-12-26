from odoo import api, models, fields, _


class HrContract(models.Model):
    _inherit = 'hr.contract'

    @api.model
    def _cron_employee_contract_reminder(self):
        contract_ids = self.search([('state', '=', 'open')])
        contract_reminder_days = self.env['ir.config_parameter'].sudo().get_param('employee_contract_reminder.contract_reminder_days')
        if not contract_reminder_days:
            raise Warning(_('Please set Contract Reminder Days in settings.'))
        for contract in contract_ids:
            if contract.date_end:
                date_end = fields.Date.from_string(contract.date_end)
                today = fields.Date.from_string(fields.Date.today())
                if (date_end - today).days <= int(contract_reminder_days):
                    template = self.env.ref('employee_contract_reminder.email_template_employee_contract_reminder')
                    template.send_mail(contract.id, force_send=True)
                    if contract.employee_id.work_email:
                        template.send_mail(contract.id, force_send=True,
                                           email_values={'email_to': contract.employee_id.work_email})
        return True
