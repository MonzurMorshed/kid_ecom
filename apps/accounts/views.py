from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.shortcuts import redirect, render, get_object_or_404
from .forms import UserRegisterForm
from .models import User


# ──────────────────────────────────────────────────────────────────────────────
# Storefront Auth
# ──────────────────────────────────────────────────────────────────────────────
def register_view(request):
    if request.user.is_authenticated:
        return redirect('custom_admin:dashboard')

    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            return redirect('accounts:login')
    else:
        form = UserRegisterForm()
    context = {
        'form': form,
    }
    return render(request, 'accounts/register.html', context)


def login_view(request):
    if request.user.is_authenticated:
        return redirect('custom_admin:dashboard')

    if request.method == 'POST':
        username_input = request.POST.get('username')
        password_input = request.POST.get('password')

        user = authenticate(request, username=username_input, password=password_input)
        if user is not None:
            if user.is_blocked:
                messages.error(request, "আপনার একাউন্টটি সাময়িকভাবে ব্লক করা হয়েছে।")
                return redirect('accounts:login')

            login(request, user)
            if user.is_staff or user.is_superuser:
                return redirect('custom_admin:dashboard')
            return redirect('/')
        else:
            messages.error(request, "ইউজারনেম বা পাসওয়ার্ড ভুল হয়েছে।")

    return render(request, 'accounts/login.html')


def logout_view(request):
    logout(request)
    messages.info(request, "আপনি সফলভাবে লগআউট করেছেন।")
    return redirect('accounts:login')


# ──────────────────────────────────────────────────────────────────────────────
# Admin — Customer List
# ──────────────────────────────────────────────────────────────────────────────
def customer_list(request):
    qs = (
        User.objects
        .filter(is_staff=False, is_superuser=False)
        .annotate(order_count=Count('orders'))
        .order_by('-id')
    )

    # ── Search ──
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(
            Q(username__icontains=q) |
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(email__icontains=q) |
            Q(phone_number__icontains=q)
        )

    # ── Status filter ──
    status = request.GET.get('status', '').strip()
    if status == 'active':
        qs = qs.filter(is_blocked=False)
    elif status == 'blocked':
        qs = qs.filter(is_blocked=True)

    # ── Summary counts (always on full base, not filtered) ──
    total_customers = User.objects.filter(is_staff=False, is_superuser=False).count()
    active_count    = User.objects.filter(is_staff=False, is_superuser=False, is_blocked=False).count()
    blocked_count   = User.objects.filter(is_staff=False, is_superuser=False, is_blocked=True).count()

    # ── Pagination ──
    paginator   = Paginator(qs, 20)
    page_number = request.GET.get('page', 1)
    page_obj    = paginator.get_page(page_number)

    context = {
        'customers':       page_obj,
        'total_customers': total_customers,
        'active_count':    active_count,
        'blocked_count':   blocked_count,
        'q':               q,
        'status':          status,
    }
    return render(request, 'custom_admin/customers/customer_list.html', context)


# ──────────────────────────────────────────────────────────────────────────────
# Admin — Customer Detail
# ──────────────────────────────────────────────────────────────────────────────
def customer_detail(request, pk):
    customer = get_object_or_404(
        User.objects.annotate(order_count=Count('orders')),
        pk=pk, is_staff=False, is_superuser=False
    )
    orders = customer.orders.order_by('-created_at')
    total_spent = orders.filter(status='DELIVERED').aggregate(
        total=Sum('total_amount')
    )['total'] or 0

    context = {
        'customer':    customer,
        'orders':      orders,
        'total_spent': total_spent,
    }
    return render(request, 'custom_admin/customers/customer_detail.html', context)


# ──────────────────────────────────────────────────────────────────────────────
# Admin — Block / Unblock Toggle
# ──────────────────────────────────────────────────────────────────────────────
def customer_block_toggle(request, pk):
    customer = get_object_or_404(User, pk=pk, is_staff=False, is_superuser=False)
    if request.method == 'POST':
        customer.is_blocked = not customer.is_blocked
        customer.save(update_fields=['is_blocked'])
        action = 'blocked' if customer.is_blocked else 'unblocked'
        messages.success(request, f'Customer "{customer.username}" has been {action}.')
    return redirect('custom_admin:customer_detail', pk=pk)