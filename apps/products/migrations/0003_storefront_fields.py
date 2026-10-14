from django.db import migrations, models


def add_storefront_fields_if_missing(apps, schema_editor):
    """
    Safely adds storefront columns if they don't already exist.
    Prevents 'Duplicate column name' error if previous migration partially ran in MySQL.
    """
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        # Category fields
        cursor.execute("SHOW COLUMNS FROM products_category")
        existing_category_cols = {row[0].lower() for row in cursor.fetchall()}

        if 'description' not in existing_category_cols:
            cursor.execute("ALTER TABLE products_category ADD COLUMN description VARCHAR(255) NOT NULL DEFAULT ''")
        if 'theme_color' not in existing_category_cols:
            cursor.execute("ALTER TABLE products_category ADD COLUMN theme_color VARCHAR(30) NOT NULL DEFAULT '#e6f0e8'")
        if 'emoji' not in existing_category_cols:
            cursor.execute("ALTER TABLE products_category ADD COLUMN emoji VARCHAR(10) NOT NULL DEFAULT ''")
        if 'display_order' not in existing_category_cols:
            cursor.execute("ALTER TABLE products_category ADD COLUMN display_order SMALLINT UNSIGNED NOT NULL DEFAULT 0")

        # Product fields
        cursor.execute("SHOW COLUMNS FROM products_product")
        existing_product_cols = {row[0].lower() for row in cursor.fetchall()}

        if 'compare_price' not in existing_product_cols:
            cursor.execute("ALTER TABLE products_product ADD COLUMN compare_price DECIMAL(10,2) NULL")
        if 'is_featured' not in existing_product_cols:
            cursor.execute("ALTER TABLE products_product ADD COLUMN is_featured TINYINT(1) NOT NULL DEFAULT 0")
        if 'is_bestseller' not in existing_product_cols:
            cursor.execute("ALTER TABLE products_product ADD COLUMN is_bestseller TINYINT(1) NOT NULL DEFAULT 0")
        if 'is_new' not in existing_product_cols:
            cursor.execute("ALTER TABLE products_product ADD COLUMN is_new TINYINT(1) NOT NULL DEFAULT 0")
        if 'rating' not in existing_product_cols:
            cursor.execute("ALTER TABLE products_product ADD COLUMN rating DECIMAL(3,1) NOT NULL DEFAULT 0.0")


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0002_add_soft_delete_to_product'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
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
                        default='',
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
            ],
            database_operations=[
                migrations.RunPython(add_storefront_fields_if_missing, migrations.RunPython.noop),
            ],
        ),
    ]
