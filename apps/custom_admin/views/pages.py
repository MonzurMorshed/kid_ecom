from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from ..decorators import permission_required
from ..forms import PageForm
from ..models import Page, ActivityLog


# ── Page Builder Views ────────────────────────────────────────────────────────

@permission_required('content')
def page_list(request):
    pages = Page.objects.all()
    suggestions = [
        'Privacy Policy', 'About Us', 'Terms & Conditions', 'Contact Us',
        'Refund Policy', 'Shipping Info', 'FAQs', 'Disclaimer',
    ]
    return render(request, 'custom_admin/pages/page_list.html', {
        'pages': pages,
        'suggestions': suggestions,
    })


@permission_required('content')
def page_create(request):
    if request.method == 'POST':
        form = PageForm(request.POST)
        if form.is_valid():
            page = form.save()
            ActivityLog.log(request, 'create', f'Created page "{page.title}"', 'Page', page.pk)
            messages.success(request, f'Page "{page.title}" created successfully.')
            return redirect('custom_admin:page_list')
    else:
        form = PageForm()
    return render(request, 'custom_admin/pages/page_form.html', {'form': form, 'action': 'Create'})


@permission_required('content')
def page_edit(request, pk):
    page = get_object_or_404(Page, pk=pk)
    if request.method == 'POST':
        form = PageForm(request.POST, instance=page)
        if form.is_valid():
            page = form.save()
            ActivityLog.log(request, 'update', f'Updated page "{page.title}"', 'Page', page.pk)
            messages.success(request, f'Page "{page.title}" updated successfully.')
            return redirect('custom_admin:page_list')
    else:
        form = PageForm(instance=page)
    return render(request, 'custom_admin/pages/page_form.html', {'form': form, 'action': 'Edit', 'page': page})


@permission_required('content')
@require_POST
def page_toggle(request, pk):
    page = get_object_or_404(Page, pk=pk)
    page.is_published = not page.is_published
    page.save(update_fields=['is_published'])
    status = 'published' if page.is_published else 'unpublished'
    messages.success(request, f'Page "{page.title}" {status}.')
    return redirect('custom_admin:page_list')


@permission_required('content')
@require_POST
def page_delete(request, pk):
    page = get_object_or_404(Page, pk=pk)
    title = page.title
    page.delete()
    ActivityLog.log(request, 'delete', f'Deleted page "{title}"', 'Page', pk)
    messages.success(request, f'Page "{title}" deleted.')
    return redirect('custom_admin:page_list')
