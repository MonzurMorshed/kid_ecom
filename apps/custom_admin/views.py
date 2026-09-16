from orders.models import Order
from accounts.models import User
from products.models import Product, Category
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from django.core.paginator import Paginator
from .decorators import admin_required
# Create your views here.
@admin_required
def dashboard(request):
    total_sales = Order.objects.filter(status='Completed').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_orders = Order.objects.count()
    active_customers = User.objects.filter(is_customer=True, is_blocked=False).count()
    low_stock_products = User.objects.filter(stock__lt=5)
    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:10]
    context = {
        'total_sales': total_sales,
        'total_orders': total_orders,
        'active_customers': active_customers,
        'low_stock_products': low_stock_products,
        'recent_orders': recent_orders,
    }
    return render(request, 'custom_admin/dashboard.html', context)

# def admin_login(request):
#     return render(request, 'custom_admin/login.html')

# def admin_logout(request):
#     return render(request, 'custom_admin/login.html')

def product_list(request):
    products = Product.objects.select_related('category').all().order_by('-created_at')
    paginator = Paginator(products, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'custom_admin/product_list.html', context)

def product_create(request):
    categories = Category.objects.filter(is_active=True)
    if request.method == 'POST':
        title = request.POST.get('title')
        slug = request.POST.get('slug')
        category_id = request.POST.get('category')
        price = request.POST.get('price')
        stock = request.POST.get('stock')
        description = request.POST.get('description')

        product = Product.objects.create(
            title=title,
            slug=slug,
            category_id=category_id,
            price=price,
            stock=stock,
            description=description,
        )

        return redirect('custom_admin:product_list')

    context = {
        'categories': categories,
    }
    return render(request, 'custom_admin/product_create.html', context)