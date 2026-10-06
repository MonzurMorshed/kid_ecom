from datetime import datetime, timedelta

from django.db.models import Sum, Count
from django.db.models.functions import TruncDate
from django.http import JsonResponse
from django.shortcuts import render

from accounts.models import User
from orders.models import Order
from products.models import Product
from ..decorators import admin_required


# ── Dashboard ─────────────────────────────────────────────────────────────────

@admin_required
def dashboard(request):
    from orders.models import OrderItem
    total_sales        = Order.objects.filter(status='DELIVERED').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_orders       = Order.objects.count()
    active_customers   = User.objects.filter(is_customer=True, is_blocked=False).count()
    low_stock_products = Product.objects.filter(stock__lt=5)
    recent_orders      = Order.objects.select_related('user').order_by('-created_at')[:10]

    # Top Selling Products (by quantity sold)
    top_selling = (
        OrderItem.objects
        .values('product__id', 'product__title', 'product__slug')
        .annotate(total_sold=Count('id'), total_qty=Sum('quantity'))
        .order_by('-total_qty')[:5]
    )

    # Order Status Breakdown (for donut chart)
    status_breakdown = (
        Order.objects
        .values('status')
        .annotate(count=Count('id'))
        .order_by('status')
    )
    status_labels = [s['status'].capitalize() for s in status_breakdown]
    status_counts = [s['count'] for s in status_breakdown]

    context = {
        'total_sales':        total_sales,
        'total_orders':       total_orders,
        'active_customers':   active_customers,
        'low_stock_products': low_stock_products,
        'recent_orders':      recent_orders,
        'top_selling':        top_selling,
        'status_labels':      status_labels,
        'status_counts':      status_counts,
    }
    return render(request, 'custom_admin/dashboard.html', context)


def revenue_chart_data(request):
    from django.utils import timezone as tz
    start_date_str = request.GET.get('start_date')
    end_date_str   = request.GET.get('end_date')

    if not start_date_str and not end_date_str:
        end_date   = tz.now().date()
        start_date = end_date - timedelta(days=6)
    else:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date   = datetime.strptime(end_date_str,   '%Y-%m-%d').date()

    orders = (
        Order.objects
        .filter(status='DELIVERED', created_at__date__range=(start_date, end_date))
        .values('created_at__date')
        .annotate(total_sales=Sum('total_amount'), date=TruncDate('created_at'))
        .order_by('created_at__date')
    )
    order_dict = {item['date'].strftime('%Y-%m-%d'): item['total_sales'] for item in orders}

    labels, data, current_date = [], [], start_date
    while current_date <= end_date:
        date_key = current_date.strftime('%Y-%m-%d')
        labels.append(current_date.strftime('%b %d'))
        data.append(order_dict.get(date_key, 0.0))
        current_date += timedelta(days=1)

    return JsonResponse({'labels': labels, 'data': data})
