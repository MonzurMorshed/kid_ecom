# Generated manually for SMS integration settings

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('custom_admin', '0011_banner_category'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesettings',
            name='sms_dummy_mode',
            field=models.BooleanField(
                default=True,
                help_text='When enabled, displays OTP on screen and accepts dummy OTP (123456) without sending real SMS',
            ),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='sms_backend',
            field=models.CharField(
                choices=[
                    ('console', 'Console / Simulation (Development / Logs only)'),
                    ('bulksmsbd', 'BulkSMSBD (Live API Gateway)'),
                ],
                default='console',
                help_text='SMS Gateway provider to use for OTP & notifications',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='sms_api_key',
            field=models.CharField(
                blank=True,
                help_text='API key provided by your SMS gateway (e.g. BulkSMSBD)',
                max_length=255,
            ),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='sms_sender_id',
            field=models.CharField(
                blank=True,
                default='Kidurabd',
                help_text='Approved Sender ID / mask name (e.g. Kidurabd or 88096...)',
                max_length=50,
            ),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='manager_sms_number',
            field=models.CharField(
                blank=True,
                help_text='Manager mobile number to receive new order SMS alerts (e.g. 017xxxxxxxx)',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='sms_order_confirm_customer',
            field=models.BooleanField(
                default=True,
                help_text='Send SMS notification to customer when order is Confirmed',
            ),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='sms_order_complete_customer',
            field=models.BooleanField(
                default=True,
                help_text='Send SMS notification to customer when order is Delivered',
            ),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='sms_order_placed_manager',
            field=models.BooleanField(
                default=True,
                help_text='Send SMS alert to store manager when a new order is placed',
            ),
        ),
    ]

