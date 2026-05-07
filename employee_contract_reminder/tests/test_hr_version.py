# -*- coding: utf-8 -*-

from dateutil.relativedelta import relativedelta
from odoo import fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestHrVersion(TransactionCase):
    """Test hr.version extension for contract reminder."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Employee = cls.env['hr.employee']
        cls.HrVersion = cls.env['hr.version']
        cls.ConfigParameter = cls.env['ir.config_parameter']

        # Create test employees with work email
        cls.employee = cls.Employee.create({
            'name': 'Test Employee',
            'work_email': 'test@example.com',
        })
        cls.employee2 = cls.Employee.create({
            'name': 'Test Employee 2',
            'work_email': 'test2@example.com',
        })

        # Set default reminder days
        cls.ConfigParameter.sudo().set_param(
            'employee_contract_reminder.contract_reminder_days', '30'
        )

    def test_get_versions_to_remind_with_valid_version(self):
        """Test that versions expiring within reminder days are found."""
        version = self.HrVersion.create({
            'employee_id': self.employee.id,
            'name': 'Test Contract Version',
            'active': True,
            'date_version': fields.Date.today() - relativedelta(days=1),
            'contract_date_start': fields.Date.today() - relativedelta(days=1),
            'contract_date_end': fields.Date.today() + relativedelta(days=15),
        })

        versions = self.HrVersion.get_versions_to_remind()
        self.assertIn(version.id, versions.ids)

    def test_get_versions_to_remind_excludes_far_future(self):
        """Test that versions beyond reminder days are not included."""
        version = self.HrVersion.create({
            'employee_id': self.employee2.id,
            'name': 'Test Version Far Future',
            'active': True,
            'date_version': fields.Date.today() - relativedelta(days=2),
            'contract_date_start': fields.Date.today() - relativedelta(days=2),
            'contract_date_end': fields.Date.today() + relativedelta(days=60),
        })

        versions = self.HrVersion.get_versions_to_remind()
        self.assertNotIn(version.id, versions.ids)

    def test_get_versions_to_remind_excludes_inactive(self):
        """Test that inactive versions are not included."""
        # Use different date_version to avoid unique constraint
        version = self.HrVersion.create({
            'employee_id': self.employee.id,
            'name': 'Test Version Inactive',
            'active': False,
            'date_version': fields.Date.today() - relativedelta(days=3),
            'contract_date_start': fields.Date.today() - relativedelta(days=3),
            'contract_date_end': fields.Date.today() + relativedelta(days=15),
        })

        versions = self.HrVersion.get_versions_to_remind()
        self.assertNotIn(version.id, versions.ids)

    def test_get_versions_to_remind_requires_contract_date_end(self):
        """Test that versions without contract_date_end are not included."""
        # Use a new employee to avoid unique constraint
        employee3 = self.Employee.create({
            'name': 'Test Employee 3',
            'work_email': 'test3@example.com',
        })
        version = self.HrVersion.create({
            'employee_id': employee3.id,
            'name': 'Test Version No End',
            'active': True,
            'date_version': fields.Date.today() - relativedelta(days=4),
            'contract_date_start': fields.Date.today() - relativedelta(days=4),
        })

        versions = self.HrVersion.get_versions_to_remind()
        self.assertNotIn(version.id, versions.ids)

    def test_get_versions_to_remind_with_no_reminder_days_set(self):
        """Test that empty reminder days parameter returns no versions."""
        self.ConfigParameter.sudo().set_param(
            'employee_contract_reminder.contract_reminder_days', ''
        )

        versions = self.HrVersion.get_versions_to_remind()
        self.assertEqual(len(versions), 0)

    def test_send_mail_reminder_template_exists(self):
        """Test that email template exists."""
        template = self.env.ref('employee_contract_reminder.email_template_employee_contract_reminder', raise_if_not_found=False)
        self.assertTrue(template, "Email template should exist")
        if template:
            self.assertEqual(template.model_id.model, 'hr.version')

    def test_cron_employee_contract_reminder_filters_no_email(self):
        """Test that cron only processes versions with work email."""
        employee_no_email = self.Employee.create({
            'name': 'No Email Employee',
        })

        version_with_email = self.HrVersion.create({
            'employee_id': self.employee.id,
            'name': 'Version With Email',
            'active': True,
            'date_version': fields.Date.today() - relativedelta(days=5),
            'contract_date_start': fields.Date.today() - relativedelta(days=5),
            'contract_date_end': fields.Date.today() + relativedelta(days=15),
        })

        version_no_email = self.HrVersion.create({
            'employee_id': employee_no_email.id,
            'name': 'Version No Email',
            'active': True,
            'date_version': fields.Date.today() - relativedelta(days=6),
            'contract_date_start': fields.Date.today() - relativedelta(days=6),
            'contract_date_end': fields.Date.today() + relativedelta(days=15),
        })

        # Mock send_mail to avoid actual email sending
        send_mail_count = 0
        original_send_mail = self.HrVersion.__class__.send_mail_reminder

        def mock_send_mail(self):
            nonlocal send_mail_count
            send_mail_count += 1

        self.HrVersion.__class__.send_mail_reminder = mock_send_mail

        try:
            result = self.HrVersion._cron_employee_contract_reminder()
            # Version with email should be in results
            self.assertIn(version_with_email.id, result.ids)
            # Version without email should NOT be in results
            self.assertNotIn(version_no_email.id, result.ids)
        finally:
            self.HrVersion.__class__.send_mail_reminder = original_send_mail
