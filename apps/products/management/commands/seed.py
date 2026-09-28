"""
Django management command to seed the database.

Usage:
    python manage.py seed
    python manage.py seed --flush   # clear existing data first

Seeds:
  - 1 admin user  (accounts.User)
  - 1 shopper user
  - 4 storefront categories  (Educational, Outdoor, Plushies, Creative)
  - 3 brands
  - 20 products  (5 per category) with storefront flags, images, variants
  - 10 orders
"""

import random
from decimal import Decimal
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify
from django.contrib.auth import get_user_model

from products.models import (
    Category, Brand, Product,
    ProductOption, ProductOptionValue, ProductVariant, ProductImage
)
from orders.models import Order, OrderItem

User = get_user_model()


class Command(BaseCommand):
    help = "Seed the database with storefront-ready sample data."

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush',
            action='store_true',
            help='Delete all existing seed data before seeding.',
        )

    def handle(self, *args, **options):
        if options['flush']:
            self.stdout.write(self.style.WARNING("Flushing existing data..."))
            OrderItem.objects.all().delete()
            Order.objects.all().delete()
            ProductVariant.objects.all().delete()
            ProductOptionValue.objects.all().delete()
            ProductOption.objects.all().delete()
            ProductImage.objects.all().delete()
            Product.objects.all().delete()
            Brand.objects.all().delete()
            Category.objects.all().delete()
            User.objects.filter(is_superuser=True).delete()

        # ── 1. Users ────────────────────────────────────────────────────────
        self.stdout.write("\n[1/5] Creating users...")
        user, created = User.objects.get_or_create(
            username='admin',
            defaults=dict(email='admin@kidecom.dev', first_name='Admin', last_name='User',
                          is_staff=True, is_superuser=True)
        )
        if created:
            user.set_password('admin1234')
            user.save()
            self._log("Created admin  (username=admin  password=admin1234)")
        else:
            self._log("Admin already exists - skipped")

        shopper, created = User.objects.get_or_create(
            username='shopper',
            defaults=dict(email='shopper@kidecom.dev', first_name='John', last_name='Doe')
        )
        if created:
            shopper.set_password('shopper1234')
            shopper.save()
            self._log("Created shopper (username=shopper  password=shopper1234)")
        else:
            self._log("Shopper already exists - skipped")

        # ── 2. Storefront Categories ─────────────────────────────────────────
        self.stdout.write("\n[2/5] Creating storefront categories...")
        CATEGORIES = [
            {
                'name': 'Educational',
                'description': 'Learn through play',
                'emoji': '📚',
                'theme_color': '#b8deeb',   # sky blue
                'display_order': 1,
            },
            {
                'name': 'Outdoor',
                'description': 'Move, explore, discover',
                'emoji': '🌿',
                'theme_color': '#bfe3d5',   # mint green
                'display_order': 2,
            },
            {
                'name': 'Plushies',
                'description': 'Soft friends for every day',
                'emoji': '🧸',
                'theme_color': '#f7c9bd',   # peach
                'display_order': 3,
            },
            {
                'name': 'Creative',
                'description': 'Make something wonderful',
                'emoji': '🎨',
                'theme_color': '#ded8f4',   # lavender
                'display_order': 4,
            },
        ]
        cat_map = {}
        for c in CATEGORIES:
            obj, created = Category.objects.get_or_create(
                name=c['name'],
                defaults={
                    'slug': slugify(c['name']),
                    'description': c['description'],
                    'emoji': c['emoji'],
                    'theme_color': c['theme_color'],
                    'display_order': c['display_order'],
                    'is_active': True,
                }
            )
            if not created:
                # Update storefront fields on existing categories
                Category.objects.filter(pk=obj.pk).update(
                    description=c['description'],
                    emoji=c['emoji'],
                    theme_color=c['theme_color'],
                    display_order=c['display_order'],
                )
                obj.refresh_from_db()
            cat_map[c['name']] = obj
            self._log(f"{c['name']}  ({'created' if created else 'updated'})")

        # ── 3. Brands ────────────────────────────────────────────────────────
        self.stdout.write("\n[3/5] Creating brands...")
        BRANDS = [
            {'name': 'LeapFrog',      'description': 'Award-winning educational toys.'},
            {'name': 'Fisher-Price',  'description': 'Trusted baby and toddler brand.'},
            {'name': 'LEGO',          'description': 'Iconic creative building sets.'},
        ]
        brand_map = {}
        for b in BRANDS:
            obj, _ = Brand.objects.get_or_create(
                name=b['name'],
                defaults={'slug': slugify(b['name']), 'is_active': True, 'description': b['description']}
            )
            brand_map[b['name']] = obj
            self._log(b['name'])

        # ── 4. Products ──────────────────────────────────────────────────────
        self.stdout.write("\n[4/5] Creating products + variants...")

        PRODUCTS = [
            # ─ Educational ─────────────────────────────────────────────────
            dict(title='Alphabet Explorer Tablet',     category='Educational', brand='LeapFrog',
                 price='1200.00', compare_price=None,
                 is_featured=True, is_bestseller=True, is_new=False, rating=Decimal('4.9'),
                 stock=30,
                 description='Interactive learning tablet that teaches letters, numbers, and phonics through 20+ fun activities.',
                 options=[('Color', ['Blue', 'Pink'])]),

            dict(title='Magnetic Letters & Numbers Set', category='Educational', brand='LeapFrog',
                 price='580.00', compare_price='750.00',
                 is_featured=False, is_bestseller=True, is_new=False, rating=Decimal('4.7'),
                 stock=60,
                 description='100-piece magnetic set for fridges and whiteboards. Teaches spelling and basic maths.',
                 options=[]),

            dict(title='Solar System Puzzle (200 pcs)', category='Educational', brand=None,
                 price='480.00', compare_price=None,
                 is_featured=True, is_bestseller=False, is_new=True, rating=Decimal('4.5'),
                 stock=45,
                 description='Glow-in-the-dark 200-piece jigsaw of the solar system. Perfect for ages 6+.',
                 options=[]),

            dict(title='Kids Microscope Kit',           category='Educational', brand=None,
                 price='950.00', compare_price='1100.00',
                 is_featured=False, is_bestseller=False, is_new=True, rating=Decimal('4.6'),
                 stock=20,
                 description='Real working microscope with 30 prepared slides. Ignite a love of science.',
                 options=[]),

            dict(title='Coding Robot for Beginners',   category='Educational', brand='LeapFrog',
                 price='1800.00', compare_price=None,
                 is_featured=True, is_bestseller=True, is_new=True, rating=Decimal('4.8'),
                 stock=15,
                 description='App-controlled coding robot that teaches programming concepts through play. Ages 5+.',
                 options=[('Color', ['Green', 'Orange'])]),

            # ─ Outdoor ─────────────────────────────────────────────────────
            dict(title='Balance Bike (12-inch)',        category='Outdoor', brand=None,
                 price='2200.00', compare_price='2600.00',
                 is_featured=True, is_bestseller=True, is_new=False, rating=Decimal('4.9'),
                 stock=25,
                 description='Lightweight balance bike with adjustable seat. Perfect first bike for ages 2–5.',
                 options=[('Color', ['Red', 'Blue', 'Green'])]),

            dict(title='Outdoor Exploration Kit',       category='Outdoor', brand=None,
                 price='650.00', compare_price=None,
                 is_featured=False, is_bestseller=True, is_new=False, rating=Decimal('4.6'),
                 stock=40,
                 description='Bug catcher, magnifying glass, compass and field journal. Adventure starts here.',
                 options=[]),

            dict(title='Splash Pad Water Mat (XXL)',   category='Outdoor', brand='Fisher-Price',
                 price='1100.00', compare_price='1400.00',
                 is_featured=True, is_bestseller=False, is_new=True, rating=Decimal('4.7'),
                 stock=30,
                 description='Extra-large splash mat for summer fun. Connects to any garden hose.',
                 options=[('Size', ['Medium', 'XL', 'XXL'])]),

            dict(title='Wooden Mud Kitchen Set',        category='Outdoor', brand=None,
                 price='1900.00', compare_price=None,
                 is_featured=False, is_bestseller=False, is_new=True, rating=Decimal('4.5'),
                 stock=12,
                 description='Solid wood outdoor mud kitchen with sink, hob and utensils. All-weather finish.',
                 options=[]),

            dict(title='Jump Rope & Sidewalk Chalk Bundle', category='Outdoor', brand=None,
                 price='380.00', compare_price=None,
                 is_featured=False, is_bestseller=True, is_new=False, rating=Decimal('4.4'),
                 stock=80,
                 description='Classic jump rope + 24-piece chalk set. Simple joys, big smiles.',
                 options=[]),

            # ─ Plushies ─────────────────────────────────────────────────────
            dict(title='Milo the Musical Bear',        category='Plushies', brand='Fisher-Price',
                 price='1250.00', compare_price=None,
                 is_featured=True, is_bestseller=True, is_new=False, rating=Decimal('4.9'),
                 stock=50,
                 description='Super-soft bear with three gentle lullabies. Machine-washable. Ages 0+.',
                 options=[('Size', ['Small', 'Large'])]),

            dict(title='Rainbow Unicorn Plush',         category='Plushies', brand=None,
                 price='890.00', compare_price='1100.00',
                 is_featured=True, is_bestseller=True, is_new=False, rating=Decimal('4.8'),
                 stock=65,
                 description='Ultra-soft rainbow unicorn with a glittery mane. The perfect gift.',
                 options=[('Color', ['Rainbow', 'Pastel Pink'])]),

            dict(title='Dino Gang Set (5 plushies)',   category='Plushies', brand=None,
                 price='1600.00', compare_price='2000.00',
                 is_featured=False, is_bestseller=False, is_new=True, rating=Decimal('4.7'),
                 stock=20,
                 description='Five adorable soft dinosaurs in a gift box. T-Rex, Stegosaurus, Triceratops and more.',
                 options=[]),

            dict(title='Ocean Friends Whale Cushion',  category='Plushies', brand=None,
                 price='750.00', compare_price=None,
                 is_featured=False, is_bestseller=True, is_new=False, rating=Decimal('4.6'),
                 stock=35,
                 description='Giant whale cushion-plush hybrid. Perfect for reading corners and cuddle time.',
                 options=[('Color', ['Blue', 'Grey'])]),

            dict(title='Calm & Cozy Weighted Bunny',   category='Plushies', brand=None,
                 price='1400.00', compare_price=None,
                 is_featured=True, is_bestseller=False, is_new=True, rating=Decimal('4.8'),
                 stock=18,
                 description='Gently weighted bunny plush that provides sensory comfort. Lavender-scented.',
                 options=[]),

            # ─ Creative ─────────────────────────────────────────────────────
            dict(title='Classic LEGO City Starter',   category='Creative', brand='LEGO',
                 price='1800.00', compare_price=None,
                 is_featured=True, is_bestseller=True, is_new=False, rating=Decimal('4.9'),
                 stock=25,
                 description='500-piece LEGO city set with vehicles, buildings, and mini-figures. Ages 6+.',
                 options=[('Set Size', ['200-pc', '500-pc'])]),

            dict(title='Watercolour Exploration Kit',  category='Creative', brand=None,
                 price='550.00', compare_price='700.00',
                 is_featured=False, is_bestseller=True, is_new=False, rating=Decimal('4.7'),
                 stock=55,
                 description='24 vibrant watercolour pans, 3 professional brushes and 30 sheets of art paper.',
                 options=[]),

            dict(title='Modelling Clay Studio (20 colours)', category='Creative', brand=None,
                 price='480.00', compare_price=None,
                 is_featured=True, is_bestseller=False, is_new=True, rating=Decimal('4.5'),
                 stock=70,
                 description='Non-toxic, air-dry modelling clay in 20 bold colours with sculpting tools.',
                 options=[]),

            dict(title='Wooden Building Blocks (100-pc)', category='Creative', brand='LeapFrog',
                 price='450.00', compare_price=None,
                 is_featured=False, is_bestseller=True, is_new=False, rating=Decimal('4.6'),
                 stock=60,
                 description='100 smooth natural-wood blocks in 10 shapes. Timeless open-ended play.',
                 options=[('Color', ['Natural', 'Painted'])]),

            dict(title='Craft & Sewing Starter Kit',   category='Creative', brand=None,
                 price='720.00', compare_price='900.00',
                 is_featured=True, is_bestseller=False, is_new=True, rating=Decimal('4.4'),
                 stock=30,
                 description='Beginner sewing kit with fabric, large needle, thread, and 5 easy patterns.',
                 options=[]),
        ]

        product_objs = []
        for pd in PRODUCTS:
            slug_base = slugify(pd['title'])
            brand_obj = brand_map.get(pd['brand']) if pd.get('brand') else None
            cat_obj = cat_map[pd['category']]
            prod, created = Product.objects.get_or_create(
                slug=slug_base,
                defaults=dict(
                    title=pd['title'],
                    category=cat_obj,
                    brand=brand_obj,
                    price=Decimal(pd['price']),
                    compare_price=Decimal(pd['compare_price']) if pd.get('compare_price') else None,
                    stock=pd['stock'],
                    is_active=True,
                    is_featured=pd['is_featured'],
                    is_bestseller=pd['is_bestseller'],
                    is_new=pd['is_new'],
                    rating=pd['rating'],
                    description=pd.get('description', ''),
                )
            )
            if not created:
                # Update storefront flags on existing products
                Product.objects.filter(pk=prod.pk).update(
                    is_featured=pd['is_featured'],
                    is_bestseller=pd['is_bestseller'],
                    is_new=pd['is_new'],
                    rating=pd['rating'],
                    compare_price=Decimal(pd['compare_price']) if pd.get('compare_price') else None,
                )
            product_objs.append(prod)
            self._log(f"{pd['title']}  [{'created' if created else 'updated'}]")

            if not created:
                continue

            # Options & variants
            for opt_name, opt_values in pd.get('options', []):
                opt_obj, _ = ProductOption.objects.get_or_create(product=prod, name=opt_name)
                for val in opt_values:
                    ProductOptionValue.objects.get_or_create(option=opt_obj, value=val)
            options = list(prod.options.prefetch_related('values').all())
            if options:
                for i, val_obj in enumerate(options[0].values.all()):
                    sku = f"{slugify(prod.title)[:12].upper()}-{i + 1:02d}"
                    v, _ = ProductVariant.objects.get_or_create(
                        product=prod, sku=sku,
                        defaults=dict(stock=max(5, pd['stock'] // 4), is_active=True)
                    )
                    v.options.add(val_obj)

        # ── 5. Orders ────────────────────────────────────────────────────────
        self.stdout.write("\n[5/5] Creating orders...")
        STATUSES = ['PENDING', 'CONFIRMED', 'PROCESSING', 'DELIVERED', 'CANCELLED']
        NAMES = ['Rahim Uddin', 'Karim Mia', 'Fatema Begum', 'Nasrin Akter', 'Shakil Ahmed',
                 'Runa Akter', 'Milon Hossain', 'Poly Khatun', 'Sumon Talukder', 'Tania Islam']
        PHONES = ['017' + str(random.randint(10000000, 99999999)) for _ in range(10)]
        ADDRS = ['12 Gulshan Ave, Dhaka', '45 Banani Rd, Dhaka', '78 Dhanmondi 27, Dhaka',
                 '3 Mirpur-10, Dhaka', '22 Uttara Sector-6, Dhaka', '9 Motijheel, Dhaka',
                 '67 Khilgaon, Dhaka', '11 Rayer Bazar, Dhaka', '5 Lalmatia, Dhaka', '30 Azimpur, Dhaka']

        for i in range(10):
            chosen = random.sample(product_objs, k=random.randint(1, 3))
            total = sum(p.price * random.randint(1, 3) for p in chosen)
            order = Order.objects.create(
                user=shopper, full_name=NAMES[i], email=f"customer{i + 1}@kidecom.dev",
                phone_number=PHONES[i], shipping_address=ADDRS[i],
                total_amount=total, status=STATUSES[i % len(STATUSES)]
            )
            Order.objects.filter(pk=order.pk).update(
                created_at=timezone.now() - timedelta(days=random.randint(0, 30))
            )
            for prod in chosen:
                OrderItem.objects.create(
                    order=order, product=prod, variant=prod.variants.first(),
                    quantity=random.randint(1, 3), price=prod.price
                )
            self._log(f"Order #{order.id}  {NAMES[i]}  {order.status}  BDT {total}")

        self.stdout.write(self.style.SUCCESS("\nSeeding complete!\n"))
        self.stdout.write("   Admin login : http://127.0.0.1:8000/django-admin/")
        self.stdout.write("   username    : admin")
        self.stdout.write("   password    : admin1234\n")
        self.stdout.write("   Storefront  : http://127.0.0.1:8000/\n")

    def _log(self, msg):
        self.stdout.write(f"  [OK] {msg}")
