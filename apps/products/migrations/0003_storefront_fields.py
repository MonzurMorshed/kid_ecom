from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0002_add_soft_delete_to_product'),
    ]

    operations = [
        # Category storefront fields
        migrations.AddField(
            model_name='category',
            name='description',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AddField(
            model_name='category',
            name='theme_color',
            field=models.CharField(
                blank=True,
                default='#e6f0e8',
                help_text="Pastel hex colour used for this category's card background.",
                max_length=30,
            ),
        ),
        migrations.AddField(
            model_name='category',
            name='emoji',
            field=models.CharField(
                blank=True,
                default='🧸',
                help_text='Single emoji representing this category.',
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name='category',
            name='display_order',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AlterModelOptions(
            name='category',
            options={
                'ordering': ['display_order', 'created_at'],
                'verbose_name': 'Category',
                'verbose_name_plural': 'Categories',
            },
        ),
        # Product storefront fields
        migrations.AddField(
            model_name='product',
            name='compare_price',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text='Original price before discount. Leave blank if not on sale.',
                max_digits=10,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='product',
            name='is_featured',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='product',
            name='is_bestseller',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='product',
            name='is_new',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='product',
            name='rating',
            field=models.DecimalField(
                decimal_places=1,
                default=0.0,
                help_text='Average rating out of 5.',
                max_digits=3,
            ),
        ),
    ]
