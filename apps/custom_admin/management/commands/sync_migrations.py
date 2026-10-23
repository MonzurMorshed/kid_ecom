from django.core.management.base import BaseCommand
from django.db import connection
from django.db.migrations.recorder import MigrationRecorder


class Command(BaseCommand):
    help = "Reconcile pre-existing schema columns and indexes with django_migrations history before migrate."

    def handle(self, *args, **options):
        recorder = MigrationRecorder(connection)
        if not recorder.has_table():
            self.stdout.write("django_migrations table not found yet. Skipping sync.")
            return

        applied = recorder.applied_migrations()

        # Check 0008: cloudflare_api_token in custom_admin_sitesettings
        m0008 = ('custom_admin', '0008_sitesettings_cloudflare_api_token_and_more')
        if m0008 not in applied:
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SHOW COLUMNS FROM `custom_admin_sitesettings` LIKE 'cloudflare_api_token'")
                    if cursor.fetchone():
                        recorder.record_applied(*m0008)
                        self.stdout.write(self.style.SUCCESS(f"[SYNC] Marked pre-existing migration as applied: {m0008[1]}"))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Could not inspect 0008: {e}"))

        # Check 0009: banner_active_pos_idx in custom_admin_banner
        m0009 = ('custom_admin', '0009_banner_active_pos_idx_and_more')
        if m0009 not in applied:
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SHOW INDEX FROM `custom_admin_banner` WHERE Key_name = 'banner_active_pos_idx'")
                    if cursor.fetchone():
                        recorder.record_applied(*m0009)
                        self.stdout.write(self.style.SUCCESS(f"[SYNC] Marked pre-existing migration as applied: {m0009[1]}"))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Could not inspect 0009: {e}"))

        # Check 0010: permissions in custom_admin_adminprofile (in case manually created)
        m0010 = ('custom_admin', '0010_adminprofile_permissions')
        if m0010 not in applied:
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SHOW COLUMNS FROM `custom_admin_adminprofile` LIKE 'permissions'")
                    if cursor.fetchone():
                        recorder.record_applied(*m0010)
                        self.stdout.write(self.style.SUCCESS(f"[SYNC] Marked pre-existing migration as applied: {m0010[1]}"))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Could not inspect 0010: {e}"))

        self.stdout.write(self.style.SUCCESS("[SYNC] Migration reconciliation complete."))
