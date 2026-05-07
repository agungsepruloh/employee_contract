{
    'name': "Employee Contract Reminder",
    'summary': """
        Automated email notifications for expiring employee contracts.
    """,
    'description': """
        This module sends automatic email reminders to employees when their
        employment contracts are approaching expiration. Configurable reminder
        period and customizable email template ensure timely notifications
        for contract renewal discussions.
    """,
    'author': "Agung Sepruloh",
    'website': "https://agungsepruloh.github.io",
    'maintainers': ['agungsepruloh'],
    'license': 'OPL-1',
    'category': 'Human Resources',
    'version': '19.0.1.0.0',
    'depends': ['base', 'hr'],
    'data': [
        'views/res_config_settings_views.xml',
        'data/ir_cron_data.xml',
        'data/mail_data.xml',
    ],
    'demo': [],
    'images': ['static/description/banner.gif'],
    'application': True,
    'installable': True,
    'price': 12.00,
    'currency': 'USD',
}
