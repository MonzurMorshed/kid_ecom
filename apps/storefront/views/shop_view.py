from decimal import Decimal
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Min, Max
from django.shortcuts import render, get_object_or_404
from products.models import Category, Product, Brand
from custom_admin.models import Banner


PAGE_SIZE = 12

FILTER_PILLS = [
    {"key": "all",        "label": "All"},
    {"key": "bestseller", "label": "Best sellers"},
    {"key": "new",        "label": "New arrivals"},
    {"key": "featured",   "label": "Featured"},
    {"key": "under25",    "label": "Under ৳2,500"},
]

SORT_CHOICES = [
    {"key": "featured",   "label": "Featured"},
    {"key": "newest",     "label": "Newest arrivals"},
    {"key": "price_asc",  "label": "Price: Low to High"},
    {"key": "price_desc", "label": "Price: High to Low"},
    {"key": "rating",     "label": "Highest Rated"},
]


class ShopView:

    @staticmethod
    def _apply_product_filters(request, base_qs):
        """Apply search, category, brand, pill, price, and sort filters to a product queryset."""
        # 1. Search Query
        q = request.GET.get("q", "").strip()
        if q:
            base_qs = base_qs.filter(
                Q(title__icontains=q)
                | Q(description__icontains=q)
                | Q(long_description__icontains=q)
                | Q(variants__sku__icontains=q)
                | Q(brand__name__icontains=q)
                | Q(category__name__icontains=q)
            ).distinct()

        # 2. Category Filter (by slug or id)
        category_slug = request.GET.get("category", "").strip()
        if category_slug:
            base_qs = base_qs.filter(
                Q(category__slug=category_slug) | Q(category__id__iexact=category_slug)
            )

        # 3. Brand Filter (by slug or id)
        brand_slug = request.GET.get("brand", "").strip()
        if brand_slug:
            base_qs = base_qs.filter(
                Q(brand__slug=brand_slug) | Q(brand__id__iexact=brand_slug)
            )

        # 4. Filter Pills
        pill = request.GET.get("filter", "all").strip().lower()
        if pill == "bestseller":
            base_qs = base_qs.filter(is_bestseller=True)
        elif pill == "new":
            base_qs = base_qs.filter(is_new=True)
        elif pill == "featured":
            base_qs = base_qs.filter(is_featured=True)
        elif pill == "under25":
            base_qs = base_qs.filter(price__lte=2500)

        # 5. Price Range
        min_price = request.GET.get("min_price", "").strip()
        max_price = request.GET.get("max_price", "").strip()
        if min_price:
            try:
                base_qs = base_qs.filter(price__gte=Decimal(min_price))
            except Exception:
                pass
        if max_price:
            try:
                base_qs = base_qs.filter(price__lte=Decimal(max_price))
            except Exception:
                pass

        # 6. Sorting
        sort = request.GET.get("sort", "featured").strip().lower()
        if sort == "newest":
            base_qs = base_qs.order_by("-created_at")
        elif sort == "price_asc":
            base_qs = base_qs.order_by("price", "-created_at")
        elif sort == "price_desc":
            base_qs = base_qs.order_by("-price", "-created_at")
        elif sort == "rating":
            base_qs = base_qs.order_by("-rating", "-created_at")
        else:  # 'featured' default
            base_qs = base_qs.order_by("-is_featured", "-rating", "-created_at")

        return base_qs, {
            "q": q,
            "category_slug": category_slug,
            "brand_slug": brand_slug,
            "pill": pill,
            "min_price": min_price,
            "max_price": max_price,
            "sort": sort,
        }

    @staticmethod
    def _paginate(request, queryset, page_size=PAGE_SIZE):
        paginator = Paginator(queryset, page_size)
        page_number = request.GET.get("page", 1)
        try:
            page_obj = paginator.get_page(page_number)
        except (PageNotAnInteger, EmptyPage):
            page_obj = paginator.get_page(1)
        return paginator, page_obj

    @staticmethod
    def _build_querystring(request):
        """Builds a query string without the 'page' parameter for clean pagination links."""
        params = request.GET.copy()
        if "page" in params:
            del params["page"]
        return params.urlencode()

    @staticmethod
    def shop(request):
        """Full product catalog & search view."""
        categories = Category.objects.filter(is_active=True, parent__isnull=True).order_by("display_order", "created_at")
        brands = Brand.objects.filter(is_active=True).order_by("name")

        base_qs = (
            Product.objects.filter(is_active=True, is_deleted=False)
            .select_related("category", "brand")
            .prefetch_related("images")
        )

        # Get global price boundaries for the slider
        price_agg = Product.objects.filter(is_active=True, is_deleted=False).aggregate(
            min_p=Min("price"), max_p=Max("price")
        )
        catalog_min_price = int(price_agg["min_p"] or 0)
        catalog_max_price = int(price_agg["max_p"] or 5000)

        # Apply filters
        filtered_qs, filter_state = ShopView._apply_product_filters(request, base_qs)
        total_count = filtered_qs.count()

        paginator, page_obj = ShopView._paginate(request, filtered_qs, PAGE_SIZE)
        querystring = ShopView._build_querystring(request)

        # Optional product listing banner
        product_top_banner = Banner.objects.filter(is_active=True, position="product_top").first()

        selected_cat = None
        if filter_state["category_slug"]:
            selected_cat = Category.objects.filter(
                Q(slug=filter_state["category_slug"]) | Q(id__iexact=filter_state["category_slug"])
            ).first()

        selected_brand = None
        if filter_state["brand_slug"]:
            selected_brand = Brand.objects.filter(
                Q(slug=filter_state["brand_slug"]) | Q(id__iexact=filter_state["brand_slug"])
            ).first()

        context = {
            "categories": categories,
            "brands": brands,
            "products": page_obj,
            "page_obj": page_obj,
            "paginator": paginator,
            "total_count": total_count,
            "querystring": querystring,
            "search_query": filter_state["q"],
            "selected_category": selected_cat,
            "selected_brand": selected_brand,
            "active_pill": filter_state["pill"],
            "filter_pills": FILTER_PILLS,
            "active_sort": filter_state["sort"],
            "sort_choices": SORT_CHOICES,
            "min_price": filter_state["min_price"],
            "max_price": filter_state["max_price"],
            "catalog_min_price": catalog_min_price,
            "catalog_max_price": catalog_max_price,
            "product_top_banner": product_top_banner,
            "announcement": "Free delivery on orders over ৳1,000 · Designed for curious little humans",
        }
        return render(request, "storefront/shop.html", context)

    @staticmethod
    def category_detail(request, category_slug):
        categories = Category.objects.filter(is_active=True, parent__isnull=True).order_by("display_order", "created_at")
        selected = get_object_or_404(Category, slug=category_slug, is_active=True)
        brands = Brand.objects.filter(is_active=True).order_by("name")

        base_qs = (
            Product.objects.filter(category=selected, is_active=True, is_deleted=False)
            .select_related("category", "brand")
            .prefetch_related("images")
        )

        # Global price bounds for this category
        price_agg = base_qs.aggregate(min_p=Min("price"), max_p=Max("price"))
        catalog_min_price = int(price_agg["min_p"] or 0)
        catalog_max_price = int(price_agg["max_p"] or 5000)

        # Apply search, brand, pill, price, sort
        filtered_qs, filter_state = ShopView._apply_product_filters(request, base_qs)
        total_count = filtered_qs.count()

        paginator, page_obj = ShopView._paginate(request, filtered_qs, PAGE_SIZE)
        querystring = ShopView._build_querystring(request)

        # Highlights for editorial showcase (when on 'all' with no filters active)
        is_default_view = not any([
            filter_state["q"],
            filter_state["brand_slug"],
            filter_state["min_price"],
            filter_state["max_price"],
            filter_state["pill"] != "all",
            filter_state["sort"] != "featured",
            request.GET.get("page"),
        ])

        most_loved = []
        new_in = []
        if is_default_view:
            most_loved = base_qs.filter(is_bestseller=True).order_by("-rating", "-created_at")[:4]
            new_in = base_qs.filter(is_new=True).order_by("-created_at")[:4]

        category_top_banner = Banner.objects.filter(is_active=True, position="category_top").first()

        selected_brand = None
        if filter_state["brand_slug"]:
            selected_brand = Brand.objects.filter(
                Q(slug=filter_state["brand_slug"]) | Q(id__iexact=filter_state["brand_slug"])
            ).first()

        context = {
            "categories": categories,
            "selected_category": selected,
            "brands": brands,
            "selected_brand": selected_brand,
            "products": page_obj,
            "page_obj": page_obj,
            "paginator": paginator,
            "total_count": total_count,
            "querystring": querystring,
            "search_query": filter_state["q"],
            "most_loved": most_loved,
            "new_in": new_in,
            "active_pill": filter_state["pill"],
            "filter_pills": FILTER_PILLS,
            "active_sort": filter_state["sort"],
            "sort_choices": SORT_CHOICES,
            "min_price": filter_state["min_price"],
            "max_price": filter_state["max_price"],
            "catalog_min_price": catalog_min_price,
            "catalog_max_price": catalog_max_price,
            "category_top_banner": category_top_banner,
            "is_default_view": is_default_view,
            "announcement": "Free delivery on orders over ৳1,000 · Designed for curious little humans",
        }
        return render(request, "storefront/category_detail.html", context)
