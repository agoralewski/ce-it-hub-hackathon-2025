"""
Item management views.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.http import JsonResponse

from warehouse.models import Shelf, Category, Item, ItemShelfAssignment
from warehouse.forms import ItemShelfAssignmentForm


@login_required
def add_item_to_shelf(request, shelf_id):
    """Add an item to a shelf"""
    shelf = get_object_or_404(
        Shelf.objects.select_related('rack', 'rack__room'), pk=shelf_id
    )

    if request.method == 'POST':
        form = ItemShelfAssignmentForm(request.POST)

        if form.is_valid():
            # Get form data
            item_name = form.cleaned_data['item_name'].strip()
            category = form.cleaned_data['category']
            manufacturer = (
                form.cleaned_data['manufacturer'].strip()
                if form.cleaned_data['manufacturer']
                else None
            )
            expiration_date = form.cleaned_data['expiration_date']
            note = form.cleaned_data['notes']
            quantity = form.cleaned_data['quantity']

            # For very large quantities, use an AJAX approach to show progress
            if quantity > 10000:
                context = {
                    'form': form,
                    'shelf': shelf,
                    'input_data': {},
                    'bulk_operation': True,
                    'quantity': quantity,
                    'item_name': item_name,
                    'category_id': category.id,
                    'manufacturer': manufacturer or '',
                    'expiration_date': expiration_date.isoformat()
                    if expiration_date
                    else '',
                    'note': note or '',
                }
                return render(request, 'warehouse/add_item.html', context)

            # Use transaction to ensure all database operations succeed or fail together
            try:
                # Determine optimal batch size based on quantity
                # Larger quantities can use larger batches for better performance
                if quantity <= 1000:
                    batch_size = 1000
                elif quantity <= 10000:
                    batch_size = 2500
                else:
                    batch_size = 5000

                start_time = timezone.now()

                # SQLite doesn't support parallel processing well due to locking
                # So we'll use the optimized single-thread approach
                with transaction.atomic():
                    remaining = quantity

                    while remaining > 0:
                        # Process in batches of batch_size or remaining items, whichever is smaller
                        current_batch = min(batch_size, remaining)

                        # Create items for this batch - use a list comprehension instead of
                        # appending in a loop for better performance
                        items_to_create = [
                            Item(
                                name=item_name,
                                category=category,
                                manufacturer=manufacturer,
                                expiration_date=expiration_date,
                                note=note,
                            )
                            for _ in range(current_batch)
                        ]

                        # Bulk create the items for this batch
                        created_items = Item.objects.bulk_create(items_to_create)

                        # Create assignments for this batch of items - use a list comprehension
                        # for better performance
                        assignments_to_create = [
                            ItemShelfAssignment(
                                item=item, shelf=shelf, added_by=request.user
                            )
                            for item in created_items
                        ]

                        # Bulk create the assignments for this batch
                        ItemShelfAssignment.objects.bulk_create(assignments_to_create)

                        # Update remaining count
                        remaining -= current_batch

                end_time = timezone.now()
                duration = (end_time - start_time).total_seconds()
                items_per_second = quantity / duration if duration > 0 else 0

                messages.success(
                    request,
                    f'{quantity} przedmiot(ów) zostało dodanych na półkę.',
                )
                return redirect('warehouse:shelf_detail', pk=shelf_id)

            except Exception as e:
                messages.error(
                    request, f'Wystąpił błąd podczas dodawania przedmiotów: {str(e)}'
                )

    else:
        # Prepopulate form fields from query parameters if present
        initial = {}
        if 'item_name' in request.GET:
            initial['item_name'] = request.GET.get('item_name', '')
        if 'category' in request.GET:
            initial['category'] = request.GET.get('category')
        if 'manufacturer' in request.GET:
            initial['manufacturer'] = request.GET.get('manufacturer', '')
        if 'notes' in request.GET:
            initial['notes'] = request.GET.get('notes', '')
        if 'expiration_date' in request.GET:
            initial['expiration_date'] = request.GET.get('expiration_date')
        form = ItemShelfAssignmentForm(initial=initial)

    # Prepare context data for the form fields
    context = {'form': form, 'shelf': shelf, 'input_data': {}, 'bulk_operation': False}

    # If this is a POST request, pass input values for Select2 fields
    if request.method == 'POST' and not form.is_valid():
        context['input_data'] = {
            'item_name': request.POST.get('item_name', ''),
            'manufacturer': request.POST.get('manufacturer', ''),
        }

    return render(request, 'warehouse/add_item.html', context)


@login_required
def remove_item_from_shelf(request, pk):
    """Remove an item from a shelf"""
    assignment = get_object_or_404(ItemShelfAssignment, pk=pk, remove_date__isnull=True)

    if request.method == 'POST':
        request.POST.get('quantity', 1)
        # Mark the assignment as removed
        assignment.remove_date = timezone.now()
        assignment.removed_by = request.user
        assignment.save()

        messages.success(request, 'Przedmiot został pomyślnie zdjęty z półki.')
        return redirect('warehouse:shelf_detail', pk=assignment.shelf.pk)

    return render(request, 'warehouse/remove_item.html', {'assignment': assignment})


@login_required
def ajax_bulk_add_items(request):
    """AJAX endpoint for adding large quantities of items with progress tracking"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)

    # Extract parameters from the request
    try:
        shelf_id = int(request.POST.get('shelf_id'))
        item_name = request.POST.get('item_name', '').strip()
        category_id = int(request.POST.get('category_id'))
        manufacturer = request.POST.get('manufacturer', '').strip() or None
        expiration_date = request.POST.get('expiration_date')
        if expiration_date and expiration_date != 'null':
            # Parse ISO format date
            from datetime import datetime

            expiration_date = datetime.fromisoformat(expiration_date).date()
        else:
            expiration_date = None
        note = request.POST.get('note', '')
        quantity = int(request.POST.get('quantity'))
        batch_size = int(request.POST.get('batch_size', 10000))
        offset = int(request.POST.get('offset', 0))
    except (ValueError, TypeError) as e:
        return JsonResponse({'error': f'Invalid parameters: {str(e)}'}, status=400)

    # Validate parameters
    if not all([shelf_id, item_name, category_id, quantity > 0]):
        return JsonResponse({'error': 'Missing required parameters'}, status=400)

    # Get shelf and category
    try:
        shelf = Shelf.objects.get(pk=shelf_id)
        category = Category.objects.get(pk=category_id)
    except (Shelf.DoesNotExist, Category.DoesNotExist):
        return JsonResponse({'error': 'Invalid shelf or category'}, status=400)

    # Calculate how many items to process in this request
    items_to_process = min(batch_size, quantity - offset)

    if items_to_process <= 0:
        # All items have been processed
        return JsonResponse(
            {
                'success': True,
                'complete': True,
                'message': f'Successfully added {quantity} items',
                'total_processed': quantity,
            }
        )

    # Use transaction to ensure all database operations succeed or fail together
    try:
        start_time = timezone.now()

        with transaction.atomic():
            # Create items for this batch
            items_to_create = [
                Item(
                    name=item_name,
                    category=category,
                    manufacturer=manufacturer,
                    expiration_date=expiration_date,
                    note=note,
                )
                for _ in range(items_to_process)
            ]

            # Bulk create the items for this batch
            created_items = Item.objects.bulk_create(items_to_create)

            # Create assignments for this batch of items
            assignments_to_create = [
                ItemShelfAssignment(item=item, shelf=shelf, added_by=request.user)
                for item in created_items
            ]

            # Bulk create the assignments for this batch
            ItemShelfAssignment.objects.bulk_create(assignments_to_create)

        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds()
        items_per_second = items_to_process / duration if duration > 0 else 0

        # Calculate progress
        new_offset = offset + items_to_process
        progress = (new_offset / quantity) * 100

        # Check if we're done
        is_complete = new_offset >= quantity

        return JsonResponse(
            {
                'success': True,
                'complete': is_complete,
                'progress': progress,
                'processed': items_to_process,
                'total_processed': new_offset,
                'remaining': quantity - new_offset,
                'duration': duration,
                'items_per_second': items_per_second,
                'offset': new_offset,  # Pass the new offset for the next batch
                'message': f'Processed {items_to_process} items in {duration:.2f} seconds ({items_per_second:.2f} items/s)',
            }
        )

    except Exception as e:
        return JsonResponse(
            {'error': f'Error processing items: {str(e)}', 'offset': offset}, status=500
        )