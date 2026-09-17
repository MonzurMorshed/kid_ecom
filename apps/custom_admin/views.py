from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum

from orders.models import Order
from accounts.models import User
from products.models import Product

from .decorators import admin_required
from .forms import AdminRegisterForm

@admin_required
def dashboard(request):
    total_sales = Order.objects.filter(status='Completed').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_orders = Order.objects.count()
    active_customers = User.objects.filter(is_customer=True, is_blocked=False).count()
    low_stock_products = Product.objects.filter(stock__lt=5)
    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:10]
    context = {
        'total_sales': total_sales,
        'total_orders': total_orders,
        'active_customers': active_customers,
        'low_stock_products': low_stock_products,
        'recent_orders': recent_orders,
    }
    return render(request, 'custom_admin/dashboard.html', context)

def admin_login(request):
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('custom_admin:dashboard')

    if request.method == 'POST':
        username_input = request.POST.get('username')
        password_input = request.POST.get('password')

        user = authenticate(request, username=username_input, password=password_input)
        if user is not None:
            if user.is_blocked:
                messages.error(request, "Your admin account has been temporarily blocked.")
                return redirect('custom_admin:login')

            if user.is_staff or user.is_superuser:
                login(request, user)
                messages.success(request, f"Welcome back, {user.username}! You have successfully logged in.")
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect('custom_admin:dashboard')
            else:
                messages.error(request, "Access denied. You do not have admin privileges.")
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, 'custom_admin/login.html')

def admin_register(request):
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('custom_admin:dashboard')

    if request.method == 'POST':
        form = AdminRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.is_staff = True
            user.is_customer = False
            user.save()
            messages.success(request, "Admin account successfully created! Please log in.")
            return redirect('custom_admin:login')
    else:
        form = AdminRegisterForm()

    return render(request, 'custom_admin/register.html', {'form': form})

def admin_logout(request):
    logout(request)
    messages.info(request, "You have been logged out of the admin panel.")
    return redirect('custom_admin:login')