# Generated manually for SMS OTP authentication

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_useraddress'),
    ]

    operations = [
        migrations.CreateModel(
            name='OTPCode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone_number', models.CharField(max_length=15)),
                ('code', models.CharField(max_length=6)),
                ('purpose', models.CharField(choices=[('signup', 'Signup'), ('reset', 'Password Reset')], max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField()),
                ('is_used', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'OTP Code',
                'ordering': ['-created_at'],
            },
        ),
    ]

