from django.contrib import messages
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, Count

from orders.models import Order
from accounts.models import User
from products.models import Product

from .decorators import admin_required
from .forms import AdminRegisterForm, ChangePasswordForm

@admin_required
def dashboard(request):
    total_sales = Order.objects.filter(status='DELIVERED').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
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


# ──────────────────────────────────────────────────────────────────────────────
# Settings — Admin User List
# ──────────────────────────────────────────────────────────────────────────────
@admin_required
def settings_admin_list(request):
    admins = (
        User.objects
        .filter(is_staff=True)
        .annotate(order_count=Count('orders'))
        .order_by('-is_superuser', 'username')
    )
    context = {
        'admins':        admins,
        'total_admins':  admins.count(),
        'superuser_count': admins.filter(is_superuser=True).count(),
    }
    return render(request, 'custom_admin/settings/admin_list.html', context)


# ──────────────────────────────────────────────────────────────────────────────
# Settings — Change Password
# ──────────────────────────────────────────────────────────────────────────────
@admin_required
def settings_change_password(request):
    if request.method == 'POST':
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            current  = form.cleaned_data['current_password']
            new_pwd  = form.cleaned_data['new_password']

            # Verify current password
            if not request.user.check_password(current):
                form.add_error('current_password', 'Current password is incorrect.')
            else:
                request.user.set_password(new_pwd)
                request.user.save()
                # Keep the user logged in after password change
                update_session_auth_hash(request, request.user)
                messages.success(request, 'Password changed successfully.')
                return redirect('custom_admin:settings_change_password')
    else:
        form = ChangePasswordForm()

    return render(request, 'custom_admin/settings/change_password.html', {'form': form})


# ──────────────────────────────────────────────────────────────────────────────
# Settings — Promote / Demote Admin
# ──────────────────────────────────────────────────────────────────────────────
@admin_required
def settings_admin_role_toggle(request, pk):
    """Toggle is_superuser (Staff -> Superuser or Superuser -> Staff)."""
    if not request.user.is_superuser:
        messages.error(request, 'Only superusers can change admin roles.')
        return redirect('custom_admin:settings_admin_list')

    admin = get_object_or_404(User, pk=pk, is_staff=True)

    # Prevent self-demotion
    if admin == request.user:
        messages.error(request, 'You cannot change your own role.')
        return redirect('custom_admin:settings_admin_list')

    if request.method == 'POST':
        admin.is_superuser = not admin.is_superuser
        admin.save(update_fields=['is_superuser'])
        role = 'Superuser' if admin.is_superuser else 'Staff'
        messages.success(request, f'"{admin.username}" is now {role}.')

    return redirect('custom_admin:settings_admin_list')


# ──────────────────────────────────────────────────────────────────────────────
# Settings — Remove Admin (revoke staff access)
# ──────────────────────────────────────────────────────────────────────────────
@admin_required
def settings_admin_remove(request, pk):
    """Remove admin privileges (set is_staff=False, is_superuser=False)."""
    if not request.user.is_superuser:
        messages.error(request, 'Only superusers can remove admins.')
        return redirect('custom_admin:settings_admin_list')

    admin = get_object_or_404(User, pk=pk, is_staff=True)

    if admin == request.user:
        messages.error(request, 'You cannot remove your own admin access.')
        return redirect('custom_admin:settings_admin_list')

    if request.method == 'POST':
        admin.is_staff       = False
        admin.is_superuser   = False
        admin.save(update_fields=['is_staff', 'is_superuser'])
        messages.success(request, f'Admin access removed for "{admin.username}".')

    return redirect('custom_admin:settings_admin_list')