# -*- coding: utf-8 -*-

from dateutil.relativedelta import relativedelta
from odoo import fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestHrContract(TransactionCase):
    """Test hr.contract extension for contract reminder."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Employee = cls.env['hr.employee']
        cls.Contract = cls.env['hr.contract']
        cls.ConfigParameter = cls.env['ir.config_parameter']

        # Create test employee with work email
        cls.employee = cls.Employee.create({
            'name': 'Test Employee',
            'work_email': 'test@example.com',
        })

        # Set default reminder days
        cls.ConfigParameter.sudo().set_param(
            'employee_contract_reminder.contract_reminder_days', '30'
        )

    def test_get_contracts_to_remind_with_valid_contract(self):
        """Test that contracts expiring within reminder days are found."""
        contract = self.Contract.create({
            'employee_id': self.employee.id,
            'name': 'Test Contract',
            'state': 'open',
            'date_start': fields.Date.today(),
            'date_end': fields.Date.today() + relativedelta(days=15),
            'wage': 5000,
        })

        contracts = self.Contract.get_contracts_to_remind()
        self.assertIn(contract.id, contracts.ids)

    def test_get_contracts_to_remind_excludes_far_future(self):
        """Test that contracts beyond reminder days are not included."""
        contract = self.Contract.create({
            'employee_id': self.employee.id,
            'name': 'Test Contract Far Future',
            'state': 'open',
            'date_start': fields.Date.today(),
            'date_end': fields.Date.today() + relativedelta(days=60),
            'wage': 5000,
        })

        contracts = self.Contract.get_contracts_to_remind()
        self.assertNotIn(contract.id, contracts.ids)

    def test_get_contracts_to_remind_excludes_non_open_state(self):
        """Test that non-open contracts are not included."""
        contract = self.Contract.create({
            'employee_id': self.employee.id,
            'name': 'Test Contract Draft',
            'state': 'draft',
            'date_start': fields.Date.today(),
            'date_end': fields.Date.today() + relativedelta(days=15),
            'wage': 5000,
        })

        contracts = self.Contract.get_contracts_to_remind()
        self.assertNotIn(contract.id, contracts.ids)

    def test_get_contracts_to_remind_requires_date_end(self):
        """Test that contracts without date_end are not included."""
        contract = self.Contract.create({
            'employee_id': self.employee.id,
            'name': 'Test Contract No End',
            'state': 'open',
            'date_start': fields.Date.today(),
            'wage': 5000,
        })

        contracts = self.Contract.get_contracts_to_remind()
        self.assertNotIn(contract.id, contracts.ids)

    def test_get_contracts_to_remind_with_no_reminder_days_set(self):
        """Test that empty reminder days parameter returns no contracts."""
        self.ConfigParameter.sudo().set_param(
            'employee_contract_reminder.contract_reminder_days', ''
        )

        contracts = self.Contract.get_contracts_to_remind()
        self.assertEqual(len(contracts), 0)

    def test_send_mail_reminder_template_exists(self):
        """Test that email template exists."""
        template = self.env.ref('employee_contract_reminder.email_template_employee_contract_reminder', raise_if_not_found=False)
        self.assertTrue(template, "Email template should exist")
        if template:
            self.assertEqual(template.model_id.model, 'hr.contract')

    def test_cron_employee_contract_reminder_filters_no_email(self):
        """Test that cron only processes contracts with work email."""
        employee_no_email = self.Employee.create({
            'name': 'No Email Employee',
        })

        contract_with_email = self.Contract.create({
            'employee_id': self.employee.id,
            'name': 'Contract With Email',
            'state': 'open',
            'date_start': fields.Date.today(),
            'date_end': fields.Date.today() + relativedelta(days=15),
            'wage': 5000,
        })

        contract_no_email = self.Contract.create({
            'employee_id': employee_no_email.id,
            'name': 'Contract No Email',
            'state': 'open',
            'date_start': fields.Date.today(),
            'date_end': fields.Date.today() + relativedelta(days=15),
            'wage': 5000,
        })

        # Mock send_mail to avoid actual email sending
        send_mail_count = 0
        original_send_mail = self.Contract.__class__.send_mail_reminder

        def mock_send_mail(self):
            nonlocal send_mail_count
            send_mail_count += 1

        self.Contract.__class__.send_mail_reminder = mock_send_mail

        try:
            result = self.Contract._cron_employee_contract_reminder()
            # Contract with email should be in results
            self.assertIn(contract_with_email.id, result.ids)
            # Contract without email should NOT be in results
            self.assertNotIn(contract_no_email.id, result.ids)
        finally:
            self.Contract.__class__.send_mail_reminder = original_send_mail
