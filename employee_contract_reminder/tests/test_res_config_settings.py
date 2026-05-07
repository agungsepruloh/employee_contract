# -*- coding: utf-8 -*-

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestResConfigSettings(TransactionCase):
    """Test res.config.settings extension for contract reminder."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ConfigSettings = cls.env['res.config.settings']

    def test_contract_reminder_days_field_exists(self):
        """Test that contract_reminder_days field exists on config settings."""
        settings = self.ConfigSettings.create({})
        self.assertTrue(hasattr(settings, 'contract_reminder_days'))

    def test_contract_reminder_days_default_value(self):
        """Test contract_reminder_days can be set and retrieved."""
        settings = self.ConfigSettings.create({})
        settings.contract_reminder_days = 30
        self.assertEqual(settings.contract_reminder_days, 30)

    def test_contract_reminder_days_stored_as_parameter(self):
        """Test that contract_reminder_days is stored as system parameter."""
        settings = self.ConfigSettings.create({})
        settings.contract_reminder_days = 45
        settings.set_values()

        param_value = self.env['ir.config_parameter'].sudo().get_param(
            'employee_contract_reminder.contract_reminder_days'
        )
        self.assertEqual(param_value, '45')
