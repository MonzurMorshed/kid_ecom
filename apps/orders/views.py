from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Order

# ──────────────────────────────────────────────────────────────────────────────
# Order List
# ──────────────────────────────────────────────────────────────────────────────
def order_list(request):
    data = Order.objects.filter(is_deleted=False).select_related('user').prefetch_related('items').order_by('-created_at')

    pending_count    = data.filter(status='PENDING').count()
    processing_count = data.filter(status='PROCESSING').count()
    confirmed_count  = data.filter(status='CONFIRMED').count()
    delivered_count  = data.filter(status='DELIVERED').count()
    cancelled_count  = data.filter(status='CANCELLED').count()

    # ── Search & Filter ──
    q      = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()

    if q:
        data = data.filter(
            Q(full_name__icontains=q)    |
            Q(email__icontains=q)        |
            Q(phone_number__icontains=q)
        )
    if status:
        data = data.filter(status=status)

    paginator   = Paginator(data, 15)
    page_number = request.GET.get('page', 1)
    page_obj    = paginator.get_page(page_number)

    context = {
        'orders':           page_obj,
        'pending_count':    pending_count,
        'processing_count': processing_count,
        'confirmed_count':  confirmed_count,
        'delivered_count':  delivered_count,
        'cancelled_count':  cancelled_count,
    }
    return render(request, 'custom_admin/orders/order_list.html', context)


# ──────────────────────────────────────────────────────────────────────────────
# Order Detail
# ──────────────────────────────────────────────────────────────────────────────
def order_detail(request, pk):
    order = get_object_or_404(
        Order.objects.select_related('user').prefetch_related('items__product', 'items__variant__options'),
        pk=pk, is_deleted=False
    )
    return render(request, 'custom_admin/orders/order_detail.html', {'order': order})


# ──────────────────────────────────────────────────────────────────────────────
# Order Invoice  (print-friendly)
# ──────────────────────────────────────────────────────────────────────────────
def order_invoice(request, pk):
    order = get_object_or_404(
        Order.objects.select_related('user').prefetch_related('items__product', 'items__variant__options'),
        pk=pk, is_deleted=False
    )
    return render(request, 'custom_admin/orders/order_invoice.html', {'order': order})


# ──────────────────────────────────────────────────────────────────────────────
# Order Update  (status + customer info)
# ──────────────────────────────────────────────────────────────────────────────
def order_update(request, pk):
    order = get_object_or_404(Order, pk=pk, is_deleted=False)

    if request.method == 'POST':
        order.status           = request.POST.get('status', order.status)
        order.full_name        = request.POST.get('full_name', order.full_name).strip()
        order.email            = request.POST.get('email', order.email).strip()
        order.phone_number     = request.POST.get('phone_number', order.phone_number).strip()
        order.shipping_address = request.POST.get('shipping_address', order.shipping_address).strip()
        order.save(update_fields=['status', 'full_name', 'email', 'phone_number', 'shipping_address', 'updated_at'])
        messages.success(request, f'Order #{order.id:05d} updated successfully.')
        return redirect('custom_admin:order_detail', pk=order.pk)

    return render(request, 'custom_admin/orders/order_update.html', {
        'order':          order,
        'status_choices': Order.STATUS_CHOICES,
    })


# ──────────────────────────────────────────────────────────────────────────────
# Order Cancel  (sets status to CANCELLED — not a soft delete)
# ──────────────────────────────────────────────────────────────────────────────
def order_cancel(request, pk):
    order = get_object_or_404(Order, pk=pk, is_deleted=False)
    if order.status not in ('CANCELLED', 'DELIVERED'):
        order.status = 'CANCELLED'
        order.save(update_fields=['status', 'updated_at'])
        messages.success(request, f'Order #{order.id:05d} has been cancelled.')
    else:
        messages.warning(request, f'Order #{order.id:05d} cannot be cancelled (already {order.status}).')
    return redirect('custom_admin:order_detail', pk=order.pk)


# ──────────────────────────────────────────────────────────────────────────────
# Order Soft Delete  (moves to trash)
# ──────────────────────────────────────────────────────────────────────────────
def order_soft_delete(request, pk):
    order = get_object_or_404(Order, pk=pk, is_deleted=False)
    order.soft_delete()
    messages.success(request, f'Order #{order.id:05d} moved to trash.')
    return redirect('custom_admin:order_list')


# ──────────────────────────────────────────────────────────────────────────────
# Order Trash  (lists soft-deleted orders)
# ──────────────────────────────────────────────────────────────────────────────
def order_trash(request):
    data = Order.objects.filter(is_deleted=True).select_related('user').order_by('-deleted_at')
    paginator   = Paginator(data, 15)
    page_number = request.GET.get('page', 1)
    page_obj    = paginator.get_page(page_number)
    return render(request, 'custom_admin/orders/order_trash.html', {'orders': page_obj})


# ──────────────────────────────────────────────────────────────────────────────
# Order Restore
# ──────────────────────────────────────────────────────────────────────────────
def order_restore(request, pk):
    order = get_object_or_404(Order, pk=pk, is_deleted=True)
    order.restore()
    messages.success(request, f'Order #{order.id:05d} has been restored.')
    return redirect('custom_admin:order_trash')


# ──────────────────────────────────────────────────────────────────────────────
# Order Permanent Delete
# ──────────────────────────────────────────────────────────────────────────────
def order_permanent_delete(request, pk):
    order = get_object_or_404(Order, pk=pk, is_deleted=True)
    order_id = order.id
    order.delete()
    messages.success(request, f'Order #{order_id:05d} permanently deleted.')
    return redirect('custom_admin:order_trash')


# ──────────────────────────────────────────────────────────────────────────────
# Export / Import / Sample CSV  (stubs — implement as needed)
# ──────────────────────────────────────────────────────────────────────────────
def order_export(request):
    return render(request, 'custom_admin/orders/order_export.html')

def order_import(request):
    return render(request, 'custom_admin/orders/order_import.html')

def order_sample_csv(request):
    return render(request, 'custom_admin/orders/order_sample_csv.html')