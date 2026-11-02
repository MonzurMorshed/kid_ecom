# Generated manually to make order email optional

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0002_order_deleted_at_order_is_deleted'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='email',
            field=models.EmailField(blank=True, default='', max_length=254),
        ),
    ]

