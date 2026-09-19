"""
Seed script for kid_ecom project.
Run from the project root:
    python seed.py

Seeds:
  - 1 admin user  (accounts.User)
  - 5 categories  (products.Category)
  - 3 brands      (products.Brand)
  - 10 products   (products.Product) with options, variants, images
  - 10 orders     (orders.Order) with items
"""

import os
import sys
import django
from decimal import Decimal

# ── project setup ──────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, 'apps'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kidurabd_env.settings')
django.setup()

# ── imports ────────────────────────────────────────────────────────────────────
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from products.models import (
    Category, Brand, Product,
    ProductOption, ProductOptionValue, ProductVariant, ProductImage
)
from orders.models import Order, OrderItem

User = get_user_model()

# ── helpers ────────────────────────────────────────────────────────────────────
def log(msg): print(f"  [OK] {msg}")

# ==============================================================================
# 1. Admin User
# ==============================================================================
print("\n[1/5] Creating admin user...")

user, created = User.objects.get_or_create(
    username='admin',
    defaults=dict(
        email='admin@kidecom.dev',
        first_name='Admin',
        last_name='User',
        is_staff=True,
        is_superuser=True,
    )
)
if created:
    user.set_password('admin1234')
    user.save()
    log("Created admin  (username=admin  password=admin1234)")
else:
    log("Admin already exists – skipped")

# Also create a regular shopper
shopper, created = User.objects.get_or_create(
    username='shopper',
    defaults=dict(
        email='shopper@kidecom.dev',
        first_name='John',
        last_name='Doe',
    )
)
if created:
    shopper.set_password('shopper1234')
    shopper.save()
    log("Created shopper (username=shopper  password=shopper1234)")
else:
    log("Shopper already exists – skipped")

# ==============================================================================
# 2. Categories
# ==============================================================================
print("\n[2/5] Creating categories...")

CATEGORIES = [
    {'name': 'Toys & Games'},
    {'name': 'Clothing', 'children': ['Boys Clothing', 'Girls Clothing']},
    {'name': 'Books'},
    {'name': 'Baby & Toddler'},
    {'name': 'Educational'},
]

cat_map = {}
for c in CATEGORIES:
    obj, _ = Category.objects.get_or_create(
        name=c['name'],
        defaults={'slug': slugify(c['name']), 'is_active': True}
    )
    cat_map[c['name']] = obj
    log(c['name'])
    for child_name in c.get('children', []):
        child, _ = Category.objects.get_or_create(
            name=child_name,
            defaults={'slug': slugify(child_name), 'parent': obj, 'is_active': True}
        )
        cat_map[child_name] = child
        log(f"   > {child_name}")

# ==============================================================================
# 3. Brands
# ==============================================================================
print("\n[3/5] Creating brands...")

BRANDS = ['LeapFrog', 'Fisher-Price', 'LEGO']
brand_map = {}
for b in BRANDS:
    obj, _ = Brand.objects.get_or_create(
        name=b,
        defaults={'slug': slugify(b), 'is_active': True,
                  'description': f'{b} – trusted kids brand.'}
    )
    brand_map[b] = obj
    log(b)

# ==============================================================================
# 4. Products
# ==============================================================================
print("\n[4/5] Creating products + variants...")

PRODUCTS = [
    dict(title='Wooden Building Blocks Set',       category='Toys & Games',    brand='LeapFrog',     price='450.00', stock=50,
         options=[('Color', ['Natural', 'Painted']), ('Pieces', ['50-pc', '100-pc'])]),
    dict(title='Interactive Learning Tablet',      category='Educational',     brand='LeapFrog',     price='1200.00', stock=30,
         options=[('Color', ['Blue', 'Pink'])]),
    dict(title='Soft Plush Elephant',              category='Baby & Toddler',  brand='Fisher-Price', price='350.00', stock=80,
         options=[('Size', ['Small', 'Large']), ('Color', ['Grey', 'Pink'])]),
    dict(title='Baby Rattle Set (6-pack)',         category='Baby & Toddler',  brand='Fisher-Price', price='280.00', stock=60),
    dict(title='Classic LEGO City Starter Pack',   category='Toys & Games',    brand='LEGO',         price='1800.00', stock=25,
         options=[('Set Size', ['200-pc', '500-pc'])]),
    dict(title='Boys Dinosaur T-Shirt',            category='Boys Clothing',   brand=None,           price='320.00', stock=100,
         options=[('Size', ['3-4Y', '5-6Y', '7-8Y']), ('Color', ['Blue', 'Green', 'Red'])]),
    dict(title='Girls Floral Dress',               category='Girls Clothing',  brand=None,           price='580.00', stock=70,
         options=[('Size', ['3-4Y', '5-6Y', '7-8Y']), ('Color', ['Pink', 'Yellow'])]),
    dict(title='Kids Story Book Bundle (5 Books)', category='Books',           brand=None,           price='750.00', stock=40),
    dict(title='Alphabet Flash Cards',             category='Educational',     brand='LeapFrog',     price='180.00', stock=120,
         options=[('Language', ['English', 'Bilingual'])]),
    dict(title='Foam Play Mat (XXL)',              category='Baby & Toddler',  brand='Fisher-Price', price='950.00', stock=35,
         options=[('Color', ['Rainbow', 'Pastel'])]),
]

product_objs = []
for pd in PRODUCTS:
    slug_base = slugify(pd['title'])
    slug = slug_base
    counter = 1
    while Product.objects.filter(slug=slug).exists():
        slug = f"{slug_base}-{counter}"
        counter += 1

    brand_obj = brand_map.get(pd['brand']) if pd.get('brand') else None
    cat_obj   = cat_map[pd['category']]

    prod, created = Product.objects.get_or_create(
        slug=slug_base,
        defaults=dict(
            title=pd['title'],
            category=cat_obj,
            brand=brand_obj,
            price=Decimal(pd['price']),
            stock=pd['stock'],
            is_active=True,
            description=f"High-quality {pd['title']} for kids of all ages.",
        )
    )
    product_objs.append(prod)
    status = "created" if created else "exists"
    log(f"{pd['title']}  [{status}]")

    if not created:
        continue

    # Options + Values + Variants
    for opt_name, opt_values in pd.get('options', []):
        opt_obj, _ = ProductOption.objects.get_or_create(product=prod, name=opt_name)
        for val in opt_values:
            ProductOptionValue.objects.get_or_create(option=opt_obj, value=val)

    # Build simple variants: one per first option's values (keep it manageable)
    options = list(prod.options.prefetch_related('values').all())
    if options:
        first_opt = options[0]
        for i, val_obj in enumerate(first_opt.values.all()):
            sku = f"{slugify(prod.title)[:12].upper()}-{i+1:02d}"
            v, _ = ProductVariant.objects.get_or_create(
                product=prod,
                sku=sku,
                defaults=dict(stock=max(5, pd['stock'] // 4), is_active=True)
            )
            v.options.add(val_obj)

# ==============================================================================
# 5. Orders
# ==============================================================================
print("\n[5/5] Creating orders...")

import random
from django.utils import timezone
from datetime import timedelta

STATUSES = ['PENDING', 'CONFIRMED', 'PROCESSING', 'DELIVERED', 'CANCELLED']
NAMES    = ['Rahim Uddin', 'Karim Mia', 'Fatema Begum', 'Nasrin Akter',
            'Shakil Ahmed', 'Runa Akter', 'Milon Hossain', 'Poly Khatun',
            'Sumon Talukder', 'Tania Islam']
PHONES   = ['017' + str(random.randint(10000000, 99999999)) for _ in range(10)]
ADDRS    = [
    '12 Gulshan Ave, Dhaka', '45 Banani Rd, Dhaka', '78 Dhanmondi 27, Dhaka',
    '3 Mirpur-10, Dhaka',   '22 Uttara Sector-6, Dhaka', '9 Motijheel, Dhaka',
    '67 Khilgaon, Dhaka',   '11 Rayer Bazar, Dhaka',     '5 Lalmatia, Dhaka',
    '30 Azimpur, Dhaka',
]

for i in range(10):
    chosen_products = random.sample(product_objs, k=random.randint(1, 3))
    items_total = sum(p.price * random.randint(1, 3) for p in chosen_products)

    order = Order.objects.create(
        user=shopper,
        full_name=NAMES[i],
        email=f"customer{i+1}@kidecom.dev",
        phone_number=PHONES[i],
        shipping_address=ADDRS[i],
        total_amount=items_total,
        status=STATUSES[i % len(STATUSES)],
    )
    # Manually set created_at to spread over last 30 days
    Order.objects.filter(pk=order.pk).update(
        created_at=timezone.now() - timedelta(days=random.randint(0, 30))
    )

    for prod in chosen_products:
        qty = random.randint(1, 3)
        variant = prod.variants.first()
        OrderItem.objects.create(
            order=order,
            product=prod,
            variant=variant,
            quantity=qty,
            price=prod.price,
        )

    log(f"Order #{order.id}  {NAMES[i]}  {order.status}  BDT {items_total}")

print("\nSeeding complete!\n")
print("   Admin login: http://127.0.0.1:8000/admin/")
print("   username : admin")
print("   password : admin1234\n")
