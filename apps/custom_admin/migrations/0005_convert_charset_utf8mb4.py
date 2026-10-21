from django.db import migrations


def convert_tables_to_utf8mb4(apps, schema_editor):
    """Convert MySQL tables to utf8mb4 so Bengali characters like ৳ can be stored."""
    if schema_editor.connection.vendor != 'mysql':
        return

    tables = [
        'custom_admin_sitesettings',
        'custom_admin_pages',
        'custom_admin_page',
        'products_product',
        'products_category',
        'orders_order',
        'storefront_contactmessage',
        'storefront_newslettersubscriber',
    ]

    with schema_editor.connection.cursor() as cursor:
        try:
            cursor.execute("ALTER DATABASE CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        except Exception:
            pass

        for table in tables:
            try:
                cursor.execute(f"SHOW TABLES LIKE '{table}'")
                if cursor.fetchone():
                    cursor.execute(f"ALTER TABLE `{table}` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            except Exception:
                pass


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('custom_admin', '0004_add_page_model'),
    ]

    operations = [
        migrations.RunPython(convert_tables_to_utf8mb4, reverse_code=reverse_noop),
    ]
