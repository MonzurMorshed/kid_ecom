# Generated manually to make order status default to CONFIRMED and remove PENDING

from django.db import migrations, models


def convert_pending_to_confirmed(apps, schema_editor):
    Order = apps.get_model('orders', 'Order')
    Order.objects.filter(status='PENDING').update(status='CONFIRMED')


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0003_alter_order_email'),
    ]

    operations = [
        migrations.RunPython(
            convert_pending_to_confirmed,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(
                choices=[
                    ('CONFIRMED', 'Confirmed'),
                    ('PROCESSING', 'Processing'),
                    ('DELIVERED', 'Delivered'),
                    ('CANCELLED', 'Cancelled'),
                ],
                default='CONFIRMED',
                max_length=50,
            ),
        ),
    ]

