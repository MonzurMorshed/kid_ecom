from django.core.management.base import BaseCommand
from products.image_optimizer import bulk_optimize_all_media


class Command(BaseCommand):
    help = "Bulk optimizes all existing images (Hero slides, Banners, Products, Variants, Categories, Brands) into configured format (e.g. WebP) and dimensions from Developer Settings."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Starting bulk image optimization..."))
        stats = bulk_optimize_all_media()
        saved_mb = round(stats['saved_bytes'] / (1024 * 1024), 2)
        saved_kb = round(stats['saved_bytes'] / 1024, 1)

        self.stdout.write(self.style.SUCCESS(
            f"\nOptimization Finished:\n"
            f"  - Total images examined : {stats['total_found']}\n"
            f"  - Successfully optimized: {stats['processed']}\n"
            f"  - Skipped (missing/none): {stats['skipped']}\n"
            f"  - Errors encountered   : {stats['errors']}\n"
            f"  - Total space saved     : {saved_mb} MB ({saved_kb} KB)\n"
        ))

        if stats['details']:
            self.stdout.write(self.style.WARNING("Details / Warnings:"))
            for d in stats['details'][:10]:
                self.stdout.write(f"  • {d}")
