from datetime import datetime, time, timedelta

from django.db.models import Sum, Count
from django.db.models.functions import TruncDate
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone as tz

from accounts.models import User
from orders.models import Order, OrderItem
from products.models import Product
from ..decorators import admin_required


# ── Dashboard ─────────────────────────────────────────────────────────────────

@admin_required
def dashboard(request):
    # Active orders queryset (exclude soft-deleted)
    orders_qs = Order.objects.filter(is_deleted=False)

    # 1. Total sales of delivered orders
    total_sales = (
        orders_qs.filter(status='DELIVERED')
        .aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    )

    # 2. Order status breakdown (also used to derive total_orders in-memory, avoiding extra COUNT query)
    status_breakdown = list(
        orders_qs
        .values('status')
        .annotate(count=Count('id'))
        .order_by('status')
    )
    total_orders  = sum(s['count'] for s in status_breakdown)
    status_labels = [s['status'].capitalize() for s in status_breakdown]
    status_counts = [s['count'] for s in status_breakdown]

    # 3. Active customers count
    active_customers = User.objects.filter(is_customer=True, is_blocked=False).count()

    # 4. Low stock products count (evaluated directly in DB without holding un-evaluated queryset)
    low_stock_count = Product.objects.filter(is_deleted=False, is_active=True, stock__lt=5).count()

    # 5. Recent orders (10 rows, select_related user to prevent N+1 queries)
    recent_orders = (
        orders_qs
        .select_related('user')
        .order_by('-created_at')[:10]
    )

    # 6. Top Selling Products (by quantity sold, only valid products & active orders)
    top_selling = (
        OrderItem.objects
        .filter(order__is_deleted=False, product__isnull=False)
        .values('product__id', 'product__title', 'product__slug')
        .annotate(total_sold=Count('id'), total_qty=Sum('quantity'))
        .order_by('-total_qty')[:5]
    )

    context = {
        'total_sales':        total_sales,
        'total_orders':       total_orders,
        'active_customers':   active_customers,
        'low_stock_count':    low_stock_count,
        'low_stock_products': low_stock_count,
        'recent_orders':      recent_orders,
        'top_selling':        top_selling,
        'status_labels':      status_labels,
        'status_counts':      status_counts,
    }
    return render(request, 'custom_admin/dashboard.html', context)


@admin_required
def revenue_chart_data(request):
    start_date_str = request.GET.get('start_date')
    end_date_str   = request.GET.get('end_date')

    today = tz.now().date()
    try:
        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date   = datetime.strptime(end_date_str,   '%Y-%m-%d').date()
            if start_date > end_date:
                start_date, end_date = end_date, start_date
        else:
            end_date   = today
            start_date = end_date - timedelta(days=6)
    except (ValueError, TypeError):
        end_date   = today
        start_date = end_date - timedelta(days=6)

    # Use timezone-aware datetime range for index-friendly querying
    start_dt = tz.make_aware(datetime.combine(start_date, time.min))
    end_dt   = tz.make_aware(datetime.combine(end_date,   time.max))

    orders = (
        Order.objects
        .filter(
            is_deleted=False,
            status='DELIVERED',
            created_at__range=(start_dt, end_dt)
        )
        .annotate(date=TruncDate('created_at'))
        .values('date')
        .annotate(total_sales=Sum('total_amount'))
        .order_by('date')
    )
    order_dict = {
        item['date'].strftime('%Y-%m-%d'): float(item['total_sales'] or 0)
        for item in orders if item['date']
    }

    labels, data, current_date = [], [], start_date
    while current_date <= end_date:
        date_key = current_date.strftime('%Y-%m-%d')
        labels.append(current_date.strftime('%b %d'))
        data.append(order_dict.get(date_key, 0.0))
        current_date += timedelta(days=1)

    return JsonResponse({'labels': labels, 'data': data})
