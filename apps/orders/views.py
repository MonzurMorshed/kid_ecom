import csv

from django.core.paginator import Paginator
from django.db.models import Q
from django.http import StreamingHttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from custom_admin.decorators import permission_required
from .models import Order

# ──────────────────────────────────────────────────────────────────────────────
# Order List
# ──────────────────────────────────────────────────────────────────────────────
@permission_required('orders')
def order_list(request):
    data = Order.objects.filter(is_deleted=False).select_related('user').prefetch_related('items').order_by('-created_at')

    pending_count    = data.filter(status='PENDING').count()
    processing_count = data.filter(status='PROCESSING').count()
    confirmed_count  = data.filter(status='CONFIRMED').count()
    delivered_count  = data.filter(status='DELIVERED').count()
    cancelled_count  = data.filter(status='CANCELLED').count()

    # ── Search & Filter ──
    q          = request.GET.get('q', '').strip()
    status     = request.GET.get('status', '').strip()
    date_from  = request.GET.get('date_from', '').strip()
    date_to    = request.GET.get('date_to', '').strip()

    if q:
        # Try numeric match for direct Order-ID lookup first
        q_filter = (
            Q(full_name__icontains=q) |
            Q(email__icontains=q)     |
            Q(phone_number__icontains=q)
        )
        if q.lstrip('#').isdigit():
            q_filter |= Q(pk=int(q.lstrip('#')))
        data = data.filter(q_filter)

    if status:
        data = data.filter(status=status)

    if date_from:
        data = data.filter(created_at__date__gte=date_from)

    if date_to:
        data = data.filter(created_at__date__lte=date_to)

    paginator   = Paginator(data, 15)
    page_number = request.GET.get('page')
    page_obj    = paginator.get_page(page_number)

    context = {
        'orders':           page_obj,
        'page_obj':         page_obj,
        'pending_count':    pending_count,
        'processing_count': processing_count,
        'confirmed_count':  confirmed_count,
        'delivered_count':  delivered_count,
        'cancelled_count':  cancelled_count,
        'status_choices':   Order.STATUS_CHOICES,
        'current_status':   status,
        'q':                q,
        'date_from':        date_from,
        'date_to':          date_to,
        'total_count':      data.count(),
    }
    return render(request, 'custom_admin/orders/order_list.html', context)


# ──────────────────────────────────────────────────────────────────────────────
# Order Detail
# ──────────────────────────────────────────────────────────────────────────────
@permission_required('orders')
def order_detail(request, pk):
    order = get_object_or_404(
        Order.objects.select_related('user').prefetch_related('items__product', 'items__variant__options'),
        pk=pk, is_deleted=False
    )
    return render(request, 'custom_admin/orders/order_detail.html', {'order': order})


# ──────────────────────────────────────────────────────────────────────────────
# Order Invoice  (print-friendly)
# ──────────────────────────────────────────────────────────────────────────────
@permission_required('orders')
def order_invoice(request, pk):
    order = get_object_or_404(
        Order.objects.select_related('user').prefetch_related('items__product', 'items__variant__options'),
        pk=pk, is_deleted=False
    )
    return render(request, 'custom_admin/orders/order_invoice.html', {'order': order})


# ──────────────────────────────────────────────────────────────────────────────
# Order Update  (status + customer info)
# ──────────────────────────────────────────────────────────────────────────────
@permission_required('orders')
def order_update(request, pk):
    order = get_object_or_404(Order, pk=pk, is_deleted=False)

    if request.method == 'POST':
        old_status             = order.status
        order.status           = request.POST.get('status', order.status)
        order.full_name        = request.POST.get('full_name', order.full_name).strip()
        order.email            = request.POST.get('email', order.email).strip()
        order.phone_number     = request.POST.get('phone_number', order.phone_number).strip()
        order.shipping_address = request.POST.get('shipping_address', order.shipping_address).strip()
        order.save(update_fields=['status', 'full_name', 'email', 'phone_number', 'shipping_address', 'updated_at'])

        # Notify customer if status changed
        if order.status != old_status:
            from .emails import send_order_status_update
            send_order_status_update(order)

        messages.success(request, f'Order #{order.id:05d} updated successfully.')
        return redirect('custom_admin:order_detail', pk=order.pk)

    return render(request, 'custom_admin/orders/order_update.html', {
        'order':          order,
        'status_choices': Order.STATUS_CHOICES,
    })


# ──────────────────────────────────────────────────────────────────────────────
# Order Cancel  (sets status to CANCELLED — not a soft delete)
# ──────────────────────────────────────────────────────────────────────────────
@permission_required('orders')
def order_cancel(request, pk):
    order = get_object_or_404(Order, pk=pk, is_deleted=False)
    if order.status not in ('CANCELLED', 'DELIVERED'):
        order.status = 'CANCELLED'
        order.save(update_fields=['status', 'updated_at'])
        from .emails import send_order_status_update
        send_order_status_update(order)
        messages.success(request, f'Order #{order.id:05d} has been cancelled.')
    else:
        messages.warning(request, f'Order #{order.id:05d} cannot be cancelled (already {order.status}).')
    return redirect('custom_admin:order_detail', pk=order.pk)


# ──────────────────────────────────────────────────────────────────────────────
# Order Soft Delete  (moves to trash)
# ──────────────────────────────────────────────────────────────────────────────
@permission_required('orders')
def order_soft_delete(request, pk):
    order = get_object_or_404(Order, pk=pk, is_deleted=False)
    order.soft_delete()
    messages.success(request, f'Order #{order.id:05d} moved to trash.')
    return redirect('custom_admin:order_list')


# ──────────────────────────────────────────────────────────────────────────────
# Order Trash  (lists soft-deleted orders)
# ──────────────────────────────────────────────────────────────────────────────
@permission_required('orders')
def order_trash(request):
    data = Order.objects.filter(is_deleted=True).select_related('user').order_by('-deleted_at')
    paginator   = Paginator(data, 15)
    page_number = request.GET.get('page', 1)
    page_obj    = paginator.get_page(page_number)
    return render(request, 'custom_admin/orders/order_trash.html', {'orders': page_obj})


# ──────────────────────────────────────────────────────────────────────────────
# Order Restore
# ──────────────────────────────────────────────────────────────────────────────
@permission_required('orders')
def order_restore(request, pk):
    order = get_object_or_404(Order, pk=pk, is_deleted=True)
    order.restore()
    messages.success(request, f'Order #{order.id:05d} has been restored.')
    return redirect('custom_admin:order_trash')


# ──────────────────────────────────────────────────────────────────────────────
# Order Permanent Delete
# ──────────────────────────────────────────────────────────────────────────────
@permission_required('orders')
def order_permanent_delete(request, pk):
    order = get_object_or_404(Order, pk=pk, is_deleted=True)
    order_id = order.id
    order.delete()
    messages.success(request, f'Order #{order_id:05d} permanently deleted.')
    return redirect('custom_admin:order_trash')


# ──────────────────────────────────────────────────────────────────────────────
# Export / Import / Sample CSV  (stubs — implement as needed)
# ──────────────────────────────────────────────────────────────────────────────
@permission_required('orders')
def order_export(request):
    """
    Stream a CSV file of orders, optionally filtered by the same
    query params used on the order list (q, status, date_from, date_to).
    """
    qs = Order.objects.filter(is_deleted=False).select_related('user').order_by('-created_at')

    q         = request.GET.get('q', '').strip()
    status    = request.GET.get('status', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to   = request.GET.get('date_to', '').strip()

    if q:
        q_filter = (
            Q(full_name__icontains=q) |
            Q(email__icontains=q)     |
            Q(phone_number__icontains=q)
        )
        if q.lstrip('#').isdigit():
            q_filter |= Q(pk=int(q.lstrip('#')))
        qs = qs.filter(q_filter)
    if status:
        qs = qs.filter(status=status)
    if date_from:
        qs = qs.filter(created_at__date__gte=date_from)
    if date_to:
        qs = qs.filter(created_at__date__lte=date_to)

    # ── Streaming CSV ──
    def _rows():
        header = [
            'Order ID', 'Status', 'Full Name', 'Email', 'Phone',
            'Shipping Address', 'Total (BDT)', 'Items', 'Created At',
        ]
        yield header
        for order in qs.prefetch_related('items'):
            yield [
                f'{order.id:05d}',
                order.status,
                order.full_name,
                order.email,
                order.phone_number,
                order.shipping_address.replace('\n', ' | '),
                str(order.total_amount),
                order.items.count(),
                order.created_at.strftime('%Y-%m-%d %H:%M'),
            ]

    class _EchoBuffer:
        """An object that implements write() and returns the written value."""
        def write(self, value):
            return value

    pseudo_buffer = _EchoBuffer()
    writer = csv.writer(pseudo_buffer)

    response = StreamingHttpResponse(
        (writer.writerow(row) for row in _rows()),
        content_type='text/csv',
    )
    filename = f'orders_{timezone.now().strftime("%Y%m%d_%H%M")}.csv'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@permission_required('orders')
def order_import(request):
    return render(request, 'custom_admin/orders/order_import.html')


@permission_required('orders')
def order_sample_csv(request):
    return render(request, 'custom_admin/orders/order_sample_csv.html')