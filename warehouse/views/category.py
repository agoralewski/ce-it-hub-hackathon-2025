"""
Category management views.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db import IntegrityError

from warehouse.models import Category, Item
from warehouse.forms import CategoryForm
from warehouse.views.utils import is_admin


@login_required
@user_passes_test(is_admin)
def category_list(request):
    """List of all categories"""
    categories = Category.objects.order_by('name')
    return render(request, 'warehouse/category_list.html', {'categories': categories})


@login_required
@user_passes_test(is_admin)
def category_create(request):
    """Create a new category"""
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Kategoria została pomyślnie utworzona.')
                return redirect('warehouse:category_list')
            except IntegrityError:
                messages.error(request, 'Kategoria o tej nazwie już istnieje.')
    else:
        form = CategoryForm()
    return render(
        request,
        'warehouse/category_form.html',
        {'form': form, 'title': 'Create Category'},
    )


@login_required
@user_passes_test(is_admin)
def category_update(request, pk):
    """Update an existing category"""
    category = get_object_or_404(Category, pk=pk)

    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Kategoria została pomyślnie zaktualizowana.')
            return redirect('warehouse:category_list')
    else:
        form = CategoryForm(instance=category)

    return render(
        request,
        'warehouse/category_form.html',
        {'form': form, 'title': 'Update Category'},
    )


@login_required
@user_passes_test(is_admin)
def category_delete(request, pk):
    """Delete a category"""
    category = get_object_or_404(Category, pk=pk)

    # Check if category has any items
    has_items = Item.objects.filter(category=category).exists()

    if request.method == 'POST':
        if 'confirm' in request.POST and not has_items:
            category.delete()
            messages.success(request, 'Kategoria została pomyślnie usunięta.')
            return redirect('warehouse:category_list')

    return render(
        request,
        'warehouse/category_delete.html',
        {'category': category, 'has_items': has_items},
    )
