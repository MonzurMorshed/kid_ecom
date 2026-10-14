"""
Seed the database with sample kids' e-commerce data.

Usage:
    python manage.py seed_data          # seed everything
    python manage.py seed_data --flush  # wipe & re-seed
"""
import random
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from accounts.models import User
from products.models import (
    Brand,
    Category,
    Product,
    ProductOption,
    ProductOptionValue,
    ProductVariant,
)
from orders.models import Order, OrderItem


class Command(BaseCommand):
    help = "Seed the database with sample kids' e-commerce data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete ALL existing data before seeding.",
        )

    # ──────────────────────────────────────────────────────────
    # Raw data
    # ──────────────────────────────────────────────────────────

    CATEGORIES = [
        {
            "name": "Toys & Games",
            "slug": "toys-games",
            "emoji": "🧸",
            "theme_color": "#fce4ec",
            "description": "Fun toys and games for all ages",
            "subcategories": [
                {"name": "Building Blocks", "slug": "building-blocks", "emoji": "🧱", "theme_color": "#fff3e0"},
                {"name": "Dolls & Action Figures", "slug": "dolls-action-figures", "emoji": "🎎", "theme_color": "#f3e5f5"},
            ],
        },
        {
            "name": "Clothing",
            "slug": "clothing",
            "emoji": "👕",
            "theme_color": "#e8f5e9",
            "description": "Trendy & comfortable kids' clothing",
            "subcategories": [
                {"name": "Boys", "slug": "boys-clothing", "emoji": "👦", "theme_color": "#e3f2fd"},
                {"name": "Girls", "slug": "girls-clothing", "emoji": "👧", "theme_color": "#fce4ec"},
            ],
        },
        {
            "name": "School Supplies",
            "slug": "school-supplies",
            "emoji": "📚",
            "theme_color": "#e3f2fd",
            "description": "Everything for school",
            "subcategories": [
                {"name": "Bags & Backpacks", "slug": "bags-backpacks", "emoji": "🎒", "theme_color": "#ede7f6"},
                {"name": "Stationery", "slug": "stationery", "emoji": "✏️", "theme_color": "#fff9c4"},
            ],
        },
        {
            "name": "Baby & Toddler",
            "slug": "baby-toddler",
            "emoji": "👶",
            "theme_color": "#fff9c4",
            "description": "Essentials for babies and toddlers",
        },
        {
            "name": "Outdoor & Sports",
            "slug": "outdoor-sports",
            "emoji": "⚽",
            "theme_color": "#e0f7fa",
            "description": "Active play and outdoor fun",
        },
    ]

    BRANDS = [
        {"name": "KidStar", "slug": "kidstar", "description": "Quality toys and games for creative kids."},
        {"name": "TinyWear", "slug": "tinywear", "description": "Comfortable and stylish kids' fashion."},
        {"name": "BrightMinds", "slug": "brightminds", "description": "Educational products that spark curiosity."},
        {"name": "PlayZone", "slug": "playzone", "description": "Outdoor and sports gear for active children."},
        {"name": "LittleSteps", "slug": "littlesteps", "description": "Premium baby and toddler essentials."},
    ]

    PRODUCTS = [
        # ── Toys & Games ──
        {
            "title": "Wooden Building Blocks Set - 100 Pieces",
            "category_slug": "building-blocks",
            "brand_slug": "kidstar",
            "price": 1250.00,
            "compare_price": 1500.00,
            "stock": 45,
            "description": "Colorful wooden building blocks to boost creativity and motor skills.",
            "long_description": "This premium 100-piece wooden building block set is designed to inspire imagination in children aged 3+. Each block is sanded smooth, painted with non-toxic colors, and sized perfectly for small hands.",
            "specifications": [
                {"label": "Pieces", "value": "100"},
                {"label": "Material", "value": "Natural Wood"},
                {"label": "Age", "value": "3+ years"},
                {"label": "Weight", "value": "1.2 kg"},
            ],
            "is_featured": True,
            "is_bestseller": True,
            "rating": 4.8,
        },
        {
            "title": "Remote Control Racing Car - Turbo Speed",
            "category_slug": "toys-games",
            "brand_slug": "playzone",
            "price": 2800.00,
            "compare_price": 3200.00,
            "stock": 30,
            "description": "High-speed RC car with rechargeable battery and cool LED lights.",
            "long_description": "Experience thrilling racing with this turbo-speed remote control car. Features 2.4GHz technology for precise control up to 50 meters, LED headlights, and a rechargeable lithium battery for 30+ minutes of play.",
            "specifications": [
                {"label": "Range", "value": "50 meters"},
                {"label": "Battery", "value": "Rechargeable Li-ion"},
                {"label": "Speed", "value": "15 km/h"},
                {"label": "Age", "value": "6+ years"},
            ],
            "is_featured": True,
            "is_new": True,
            "rating": 4.5,
        },
        {
            "title": "Princess Doll with Accessories",
            "category_slug": "dolls-action-figures",
            "brand_slug": "kidstar",
            "price": 950.00,
            "stock": 60,
            "description": "Beautiful princess doll with changeable outfits and accessories.",
            "long_description": "This adorable princess doll comes with 3 gorgeous outfits, a tiara, shoes, and a handbag. The doll has moveable joints and silky hair that can be styled.",
            "specifications": [
                {"label": "Height", "value": "30 cm"},
                {"label": "Accessories", "value": "12 pieces"},
                {"label": "Age", "value": "3+ years"},
            ],
            "is_bestseller": True,
            "rating": 4.6,
        },
        # ── Clothing ──
        {
            "title": "Boys Casual Polo T-Shirt",
            "category_slug": "boys-clothing",
            "brand_slug": "tinywear",
            "price": 650.00,
            "compare_price": 800.00,
            "stock": 0,  # managed via variants
            "description": "Soft cotton polo t-shirt for everyday comfort.",
            "long_description": "Made from 100% premium cotton, this polo t-shirt is breathable, soft, and perfect for everyday wear. Available in multiple sizes and colors.",
            "specifications": [
                {"label": "Material", "value": "100% Cotton"},
                {"label": "Care", "value": "Machine Washable"},
            ],
            "is_featured": True,
            "rating": 4.3,
            "variants": {
                "Size": ["S (3-4Y)", "M (5-6Y)", "L (7-8Y)", "XL (9-10Y)"],
                "Color": ["Navy Blue", "White", "Red"],
            },
        },
        {
            "title": "Girls Floral Summer Dress",
            "category_slug": "girls-clothing",
            "brand_slug": "tinywear",
            "price": 1100.00,
            "compare_price": 1400.00,
            "stock": 0,
            "description": "Cute floral print dress perfect for summer outings.",
            "long_description": "A beautiful floral summer dress with a comfortable cotton lining. Features a bow detail at the waist and a twirl-worthy skirt that every little girl will love.",
            "specifications": [
                {"label": "Material", "value": "Cotton Blend"},
                {"label": "Pattern", "value": "Floral Print"},
                {"label": "Season", "value": "Summer"},
            ],
            "is_new": True,
            "is_featured": True,
            "rating": 4.7,
            "variants": {
                "Size": ["2-3Y", "4-5Y", "6-7Y", "8-9Y"],
                "Color": ["Pink Floral", "Yellow Floral"],
            },
        },
        # ── School Supplies ──
        {
            "title": "Dinosaur Print School Backpack",
            "category_slug": "bags-backpacks",
            "brand_slug": "brightminds",
            "price": 1800.00,
            "compare_price": 2100.00,
            "stock": 35,
            "description": "Lightweight and durable backpack with cool dinosaur print.",
            "long_description": "This ergonomic school backpack features a fun dinosaur print, padded shoulder straps, multiple compartments, and a water bottle side pocket. Waterproof material keeps books safe on rainy days.",
            "specifications": [
                {"label": "Capacity", "value": "25 Liters"},
                {"label": "Material", "value": "Waterproof Polyester"},
                {"label": "Compartments", "value": "3 + side pockets"},
                {"label": "Weight", "value": "450g"},
            ],
            "is_bestseller": True,
            "rating": 4.4,
        },
        {
            "title": "Premium Color Pencil Set - 48 Shades",
            "category_slug": "stationery",
            "brand_slug": "brightminds",
            "price": 450.00,
            "stock": 100,
            "description": "Professional-grade color pencils in a beautiful tin case.",
            "long_description": "Unleash your child's inner artist with this set of 48 vibrant color pencils. Features smooth, break-resistant leads and comes in a reusable metal tin.",
            "specifications": [
                {"label": "Colors", "value": "48"},
                {"label": "Lead Type", "value": "Soft Core"},
                {"label": "Case", "value": "Metal Tin"},
            ],
            "is_new": True,
            "rating": 4.2,
        },
        # ── Baby & Toddler ──
        {
            "title": "Soft Plush Elephant - Musical Toy",
            "category_slug": "baby-toddler",
            "brand_slug": "littlesteps",
            "price": 850.00,
            "stock": 40,
            "description": "Cuddly plush elephant that plays soothing lullabies.",
            "long_description": "This super-soft plush elephant is a perfect companion for babies. Press its tummy to hear gentle lullabies. Made from hypoallergenic materials and machine washable.",
            "specifications": [
                {"label": "Size", "value": "25 cm"},
                {"label": "Material", "value": "Hypoallergenic Plush"},
                {"label": "Battery", "value": "2x AAA (included)"},
                {"label": "Age", "value": "0+ months"},
            ],
            "is_featured": True,
            "is_bestseller": True,
            "rating": 4.9,
        },
        {
            "title": "Baby Walker with Activity Center",
            "category_slug": "baby-toddler",
            "brand_slug": "littlesteps",
            "price": 3500.00,
            "compare_price": 4200.00,
            "stock": 20,
            "description": "Multi-functional baby walker with fun activities and music.",
            "long_description": "Help your baby take their first steps with this colorful walker. Features removable activity panel with lights, music, shape sorters, and spinning gears. Adjustable speed control for safety.",
            "specifications": [
                {"label": "Age", "value": "6-18 months"},
                {"label": "Weight Capacity", "value": "15 kg"},
                {"label": "Material", "value": "BPA-free Plastic"},
                {"label": "Features", "value": "Music, Lights, Shape Sorter"},
            ],
            "is_new": True,
            "rating": 4.6,
        },
        # ── Outdoor & Sports ──
        {
            "title": "Kids Football - Size 3",
            "category_slug": "outdoor-sports",
            "brand_slug": "playzone",
            "price": 550.00,
            "stock": 75,
            "description": "Durable and lightweight football perfect for young players.",
            "long_description": "Official size 3 football designed specifically for children aged 5-8. Made with durable TPU material and machine-stitched panels for consistent flight and bounce.",
            "specifications": [
                {"label": "Size", "value": "3 (Junior)"},
                {"label": "Material", "value": "TPU"},
                {"label": "Weight", "value": "300g"},
                {"label": "Age", "value": "5-8 years"},
            ],
            "rating": 4.1,
        },
    ]

    ORDERS_DATA = [
        {
            "status": "DELIVERED",
            "full_name": "Rahim Uddin",
            "email": "rahim@example.com",
            "phone": "01712345678",
            "address": "House 12, Road 5, Dhanmondi, Dhaka",
            "items": [
                {"product_idx": 0, "qty": 1},
                {"product_idx": 6, "qty": 2},
            ],
        },
        {
            "status": "PROCESSING",
            "full_name": "Fatima Akter",
            "email": "fatima@example.com",
            "phone": "01898765432",
            "address": "Flat 4B, Green Tower, Uttara, Dhaka",
            "items": [
                {"product_idx": 7, "qty": 1},
                {"product_idx": 2, "qty": 1},
            ],
        },
        {
            "status": "PENDING",
            "full_name": "Karim Hossain",
            "email": "karim@example.com",
            "phone": "01555123456",
            "address": "Village Char Bata, Comilla",
            "items": [
                {"product_idx": 5, "qty": 1},
                {"product_idx": 9, "qty": 3},
            ],
        },
        {
            "status": "CONFIRMED",
            "full_name": "Nusrat Jahan",
            "email": "nusrat@example.com",
            "phone": "01622334455",
            "address": "42/A, Agrabad C/A, Chittagong",
            "items": [
                {"product_idx": 1, "qty": 1},
            ],
        },
        {
            "status": "CANCELLED",
            "full_name": "Arif Rahman",
            "email": "arif@example.com",
            "phone": "01777888999",
            "address": "Sonadanga, Khulna",
            "items": [
                {"product_idx": 8, "qty": 1},
                {"product_idx": 3, "qty": 2},
            ],
        },
    ]

    # ──────────────────────────────────────────────────────────
    # Main handler
    # ──────────────────────────────────────────────────────────

    def handle(self, *args, **options):
        if options["flush"]:
            self.stdout.write(self.style.WARNING("Flushing existing data..."))
            OrderItem.objects.all().delete()
            Order.objects.all().delete()
            ProductVariant.objects.all().delete()
            ProductOptionValue.objects.all().delete()
            ProductOption.objects.all().delete()
            Product.objects.all().delete()
            Category.objects.all().delete()
            Brand.objects.all().delete()

        admin_user = self._create_admin()
        categories = self._create_categories()
        brands = self._create_brands()
        products = self._create_products(categories, brands)
        self._create_orders(admin_user, products)

        self.stdout.write(self.style.SUCCESS("\n[OK] Seeding complete!"))

    # ──────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────

    def _create_admin(self):
        user, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@kidurabd.com",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created:
            user.set_password("admin123")
            user.save()
            self.stdout.write(self.style.SUCCESS("[+] Superuser created: admin / admin123"))
        else:
            self.stdout.write("[*] Superuser 'admin' already exists -- skipped.")
        return user

    def _create_categories(self):
        cat_map = {}
        order = 0
        for data in self.CATEGORIES:
            order += 1
            parent, _ = Category.objects.get_or_create(
                slug=data["slug"],
                defaults={
                    "name": data["name"],
                    "emoji": data.get("emoji", "🧸"),
                    "theme_color": data.get("theme_color", "#e6f0e8"),
                    "description": data.get("description", ""),
                    "display_order": order,
                },
            )
            cat_map[data["slug"]] = parent

            for sub in data.get("subcategories", []):
                child, _ = Category.objects.get_or_create(
                    slug=sub["slug"],
                    defaults={
                        "name": sub["name"],
                        "parent": parent,
                        "emoji": sub.get("emoji", "🧸"),
                        "theme_color": sub.get("theme_color", "#e6f0e8"),
                        "display_order": order,
                    },
                )
                cat_map[sub["slug"]] = child

        self.stdout.write(f"[+] Categories: {len(cat_map)} ready")
        return cat_map

    def _create_brands(self):
        brand_map = {}
        for data in self.BRANDS:
            brand, _ = Brand.objects.get_or_create(
                slug=data["slug"],
                defaults={
                    "name": data["name"],
                    "description": data.get("description", ""),
                },
            )
            brand_map[data["slug"]] = brand

        self.stdout.write(f"[+] Brands: {len(brand_map)} ready")
        return brand_map

    def _create_products(self, categories, brands):
        created_products = []
        for data in self.PRODUCTS:
            slug = slugify(data["title"], allow_unicode=True)

            product, created = Product.objects.get_or_create(
                slug=slug,
                defaults={
                    "title": data["title"],
                    "category": categories[data["category_slug"]],
                    "brand": brands.get(data.get("brand_slug")),
                    "price": Decimal(str(data["price"])),
                    "compare_price": Decimal(str(data["compare_price"])) if data.get("compare_price") else None,
                    "stock": data.get("stock", 0),
                    "description": data.get("description", ""),
                    "long_description": data.get("long_description", ""),
                    "specifications": data.get("specifications", []),
                    "is_featured": data.get("is_featured", False),
                    "is_bestseller": data.get("is_bestseller", False),
                    "is_new": data.get("is_new", False),
                    "rating": Decimal(str(data.get("rating", 0))),
                },
            )

            # Create variants if defined
            if created and "variants" in data:
                self._create_variants(product, data["variants"])

            created_products.append(product)

        self.stdout.write(f"[+] Products: {len(created_products)} ready")
        return created_products

    def _create_variants(self, product, variant_data):
        """
        variant_data example:
        {
            "Size": ["S", "M", "L"],
            "Color": ["Red", "Blue"],
        }
        Creates options, values, and all variant combinations.
        """
        option_values_map = {}  # {"Size": [val_obj_S, val_obj_M, ...], ...}

        for option_name, values in variant_data.items():
            option, _ = ProductOption.objects.get_or_create(
                product=product,
                name=option_name,
            )
            option_values_map[option_name] = []
            for val in values:
                val_obj, _ = ProductOptionValue.objects.get_or_create(
                    option=option,
                    value=val,
                )
                option_values_map[option_name].append(val_obj)

        # Build all combinations
        import itertools

        option_names = list(option_values_map.keys())
        value_lists = [option_values_map[n] for n in option_names]
        combo_count = 0

        for combo in itertools.product(*value_lists):
            combo_count += 1
            sku_parts = [product.slug[:15]]
            for val_obj in combo:
                sku_parts.append(slugify(val_obj.value)[:8])
            sku = "-".join(sku_parts)

            # Ensure unique SKU
            if ProductVariant.objects.filter(sku=sku).exists():
                sku = f"{sku}-{combo_count}"

            variant = ProductVariant.objects.create(
                product=product,
                sku=sku,
                stock=random.randint(5, 25),
                is_active=True,
            )
            variant.options.set(combo)

        self.stdout.write(f"   -> {product.title}: {combo_count} variants created")

    def _create_orders(self, admin_user, products):
        order_count = 0
        for data in self.ORDERS_DATA:
            total = Decimal("0.00")
            items_to_create = []

            for item_data in data["items"]:
                idx = item_data["product_idx"]
                if idx >= len(products):
                    continue
                prod = products[idx]
                qty = item_data["qty"]
                price = prod.price
                total += price * qty
                items_to_create.append((prod, qty, price))

            order = Order.objects.create(
                user=admin_user,
                full_name=data["full_name"],
                email=data["email"],
                phone_number=data["phone"],
                shipping_address=data["address"],
                total_amount=total,
                status=data["status"],
            )

            for prod, qty, price in items_to_create:
                OrderItem.objects.create(
                    order=order,
                    product=prod,
                    quantity=qty,
                    price=price,
                )

            order_count += 1

        self.stdout.write(f"[+] Orders: {order_count} ready")
