"""
Item management views.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.http import JsonResponse
from django.urls import reverse

from warehouse.models import Shelf, Category, Item, ItemShelfAssignment, Room
from warehouse.forms import ItemShelfAssignmentForm
from warehouse.views.location import (
    batch_move_items_between_shelves,
    move_item_between_shelves,
)


@login_required
def add_item_to_shelf(request, shelf_id):
    """Add an item to a shelf"""
    shelf = get_object_or_404(
        Shelf.objects.select_related('rack', 'rack__room'), pk=shelf_id
    )

    # Get the next URL if provided, or default to item_list
    next_url = request.GET.get('next', '')

    if request.method == 'POST':
        form = ItemShelfAssignmentForm(request.POST)

        # Get the next URL from POST if available
        next_url = request.POST.get('next', next_url)

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
                    'next': next_url,  # Pass along the next URL
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

                messages.success(
                    request,
                    f'{quantity} przedmiot(ów) zostało dodanych na półkę.',
                )

                # Redirect to the next URL if provided, otherwise to shelf detail
                if next_url:
                    return redirect(next_url)
                else:
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
    context = {
        'form': form,
        'shelf': shelf,
        'input_data': {},
        'bulk_operation': False,
        'next': next_url,  # Pass the next URL to the template
    }

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
    item_name = assignment.item.name
    shelf_id = assignment.shelf.pk

    # Get the next URL if provided, or default to shelf detail
    next_url = request.GET.get('next', '')

    # Get all active assignments for this item on this shelf that match the same properties
    matching_assignments = ItemShelfAssignment.objects.filter(
        item__name=item_name,
        shelf_id=shelf_id,
        remove_date__isnull=True,
        item__category=assignment.item.category,
        item__manufacturer=assignment.item.manufacturer,
        item__expiration_date=assignment.item.expiration_date,
        item__note=assignment.item.note,
    ).select_related('item')

    total_available = matching_assignments.count()

    if request.method == 'POST':
        # Get the next URL from POST if available
        next_url = request.POST.get('next', next_url)

        quantity = int(request.POST.get('quantity', 1))
        # Ensure quantity doesn't exceed available items
        quantity = min(quantity, total_available)

        # For very large quantities, use an AJAX approach to show progress
        if quantity > 1000:  # More reasonable threshold for production
            print(f'Assignment PK: {assignment.pk}')
            context = {
                'assignment': assignment,
                'total_available': total_available,
                'bulk_operation': True,
                'quantity': quantity,
                'assignment_id': assignment.pk,  # Add explicit assignment_id
                'next': next_url,  # Pass along the next URL
            }
            return render(request, 'warehouse/remove_item.html', context)

        # Mark the specified number of assignments as removed
        assignments_to_remove = matching_assignments[:quantity]
        for assignment_to_remove in assignments_to_remove:
            assignment_to_remove.remove_date = timezone.now()
            assignment_to_remove.removed_by = request.user
            assignment_to_remove.save()

        messages.success(
            request,
            f'{quantity} przedmiot(ów) "{item_name}" zostało pomyślnie zdjętych z półki.',
        )

        # Redirect to the next URL if provided, otherwise to shelf detail
        if next_url:
            return redirect(next_url)
        else:
            return redirect('warehouse:shelf_detail', pk=shelf_id)

    return render(
        request,
        'warehouse/remove_item.html',
        {
            'assignment': assignment,
            'total_available': total_available,
            'bulk_operation': False,
            'next': next_url,  # Pass the next URL to the template
        },
    )


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
        # Get the next URL if provided
        next_url = request.POST.get('next', '')
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
        # Get the next URL if provided
        next_url = request.POST.get('next', '')
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
                'next_url': next_url,
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


@login_required
def ajax_bulk_remove_items(request):
    """AJAX endpoint for removing large quantities of items with progress tracking"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)

    # Extract parameters from the request
    try:
        assignment_id = int(request.POST.get('assignment_id', 0))
        quantity = int(request.POST.get('quantity', 0))
        batch_size = int(request.POST.get('batch_size', 5000))
        offset = int(request.POST.get('offset', 0))
        # Get the next URL if provided
        next_url = request.POST.get('next', '')

        # Debug information
        print(f'Request POST data: {request.POST}')
        print(f'Assignment ID: {assignment_id}')
    except (ValueError, TypeError) as e:
        return JsonResponse({'error': f'Invalid parameters: {str(e)}'}, status=400)

    # Validate parameters
    if not all([assignment_id, quantity > 0]):
        return JsonResponse({'error': 'Missing required parameters'}, status=400)

    # Get the assignment
    try:
        # Try to get the assignment, first by looking for one that's not removed
        try:
            assignment = ItemShelfAssignment.objects.get(
                pk=assignment_id, remove_date__isnull=True
            )
        except ItemShelfAssignment.DoesNotExist:
            # If that fails, look for any assignment with this ID, even if it's already removed
            assignment = ItemShelfAssignment.objects.get(pk=assignment_id)
            print(f'Found assignment {assignment.pk} but it was already removed')
    except ItemShelfAssignment.DoesNotExist:
        return JsonResponse(
            {'error': f'Invalid assignment ID: {assignment_id}'}, status=400
        )

    # Get all matching assignments
    try:
        matching_assignments = ItemShelfAssignment.objects.filter(
            item__name=assignment.item.name,
            shelf_id=assignment.shelf.pk,
            remove_date__isnull=True,
            item__category=assignment.item.category,
            item__manufacturer=assignment.item.manufacturer,
            item__expiration_date=assignment.item.expiration_date,
            item__note=assignment.item.note,
        ).select_related('item')

        total_available = matching_assignments.count()

        if total_available == 0:
            return JsonResponse(
                {'error': 'No matching items available for removal'}, status=400
            )
    except Exception as e:
        return JsonResponse(
            {'error': f'Error finding matching assignments: {str(e)}'}, status=400
        )

    # Calculate how many items to process in this request
    items_to_process = min(batch_size, quantity - offset)

    if items_to_process <= 0:
        # All items have been processed
        return JsonResponse(
            {
                'success': True,
                'complete': True,
                'message': f'Successfully removed {quantity} items',
                'total_processed': quantity,
                'remaining': 0,
                'progress': 100,
                'next': next_url
            }
        )

    # Use transaction to ensure all database operations succeed or fail together
    try:
        start_time = timezone.now()

        with transaction.atomic():
            # Get the batch of assignments to remove
            assignments_to_remove = list(matching_assignments[0:items_to_process])

            # Mark all assignments in this batch as removed
            current_time = timezone.now()
            for assignment_to_remove in assignments_to_remove:
                assignment_to_remove.remove_date = current_time
                assignment_to_remove.removed_by = request.user
                assignment_to_remove.save(update_fields=['remove_date', 'removed_by'])

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


@login_required
def add_new_item(request):
    """Add a new item with shelf selection - first step: select location"""
    # Get the next URL if provided (where to return after the whole process)
    next_url = request.GET.get('next', '')

    if request.method == 'POST':
        # Get the selected shelf ID from POST data
        shelf_id = request.POST.get('shelf')
        # Get the next URL from POST if available
        next_url = request.POST.get('next', next_url)

        if not shelf_id:
            messages.error(request, 'Proszę wybrać półkę.')
            return render(
                request,
                'warehouse/add_new_item.html',
                {'rooms': Room.objects.all().order_by('name'), 'next': next_url},
            )

        # Redirect to add_item_to_shelf with the selected shelf and next parameter
        url = reverse('warehouse:add_item_to_shelf', kwargs={'shelf_id': shelf_id})
        if next_url:
            url = f'{url}?next={next_url}'
        return redirect(url)
    else:
        # Just show the room/rack/shelf selection form
        return render(
            request,
            'warehouse/add_new_item.html',
            {'rooms': Room.objects.all().order_by('name'), 'next': next_url},
        )


@login_required
def move_group_items(request):
    """Move a group of items to a different shelf."""
    # Get parameters from request
    source_shelf_id = request.GET.get('shelf_id')
    item_name = request.GET.get('item_name')
    category_id = request.GET.get('category')
    manufacturer = request.GET.get('manufacturer')
    expiration_date = request.GET.get('expiration_date')

    # Validate that we have the required information
    if not all([source_shelf_id, item_name, category_id]):
        messages.error(request, 'Brakuje wymaganych parametrów.')
        return redirect('warehouse:item_list')

    source_shelf = get_object_or_404(
        Shelf.objects.select_related('rack', 'rack__room'), pk=source_shelf_id
    )
    category = get_object_or_404(Category, pk=category_id)

    # Find all items matching the criteria
    matching_items = Item.objects.filter(
        name=item_name,
        category=category,
        manufacturer=manufacturer if manufacturer else None,
        expiration_date=expiration_date if expiration_date else None,
    )

    # Find all active assignments for these items on the source shelf
    matching_assignments = ItemShelfAssignment.objects.filter(
        item__in=matching_items, shelf=source_shelf, remove_date__isnull=True
    ).select_related('item')

    items_count = matching_assignments.count()

    if request.method == 'POST':
        # Process form submission - get the target shelf ID
        target_shelf_id = request.POST.get('shelf')

        if not target_shelf_id:
            messages.error(request, 'Proszę wybrać półkę docelową.')
            # Get all rooms to repopulate the form
            rooms = Room.objects.all().order_by('name')
            return render(
                request,
                'warehouse/move_items.html',
                {
                    'rooms': rooms,
                    'source_shelf': source_shelf,
                    'item_name': item_name,
                    'category': category,
                    'manufacturer': manufacturer,
                    'expiration_date': expiration_date,
                    'items_count': items_count,
                },
            )

        # Don't allow moving to the same shelf
        if int(target_shelf_id) == int(source_shelf_id):
            messages.error(request, 'Nie można przenieść przedmiotów na tę samą półkę.')
            rooms = Room.objects.all().order_by('name')
            return render(
                request,
                'warehouse/move_items.html',
                {
                    'rooms': rooms,
                    'source_shelf': source_shelf,
                    'item_name': item_name,
                    'category': category,
                    'manufacturer': manufacturer,
                    'expiration_date': expiration_date,
                    'items_count': items_count,
                },
            )

        # Get list of item IDs to move
        item_ids = [assignment.item_id for assignment in matching_assignments]

        # Execute the move
        with transaction.atomic():
            moved_count, new_assignments, errors = batch_move_items_between_shelves(
                item_ids=item_ids,
                from_shelf_id=source_shelf_id,
                to_shelf_id=target_shelf_id,
                user=request.user,
            )

            # Display any errors
            for error in errors:
                messages.warning(request, error)

            target_shelf = get_object_or_404(Shelf, pk=target_shelf_id)

            if moved_count > 0:
                messages.success(
                    request,
                    f'{moved_count} przedmiot(ów) "{item_name}" zostało pomyślnie przeniesionych na półkę {target_shelf.full_location}.',
                )
                return redirect('warehouse:shelf_detail', pk=target_shelf_id)
            else:
                messages.warning(
                    request, 'Nie udało się przenieść żadnych przedmiotów.'
                )
                return redirect('warehouse:item_list')

    # GET request - show the form to select target location
    rooms = Room.objects.all().order_by('name')

    return render(
        request,
        'warehouse/move_items.html',
        {
            'rooms': rooms,
            'source_shelf': source_shelf,
            'item_name': item_name,
            'category': category,
            'manufacturer': manufacturer,
            'expiration_date': expiration_date,
            'items_count': items_count,
        },
    )


@login_required
def move_single_item(request, assignment_id):
    """Move a single item to a different shelf."""
    # Get the assignment
    assignment = get_object_or_404(
        ItemShelfAssignment.objects.select_related(
            'item', 'shelf', 'shelf__rack', 'shelf__rack__room', 'item__category'
        ),
        pk=assignment_id,
        remove_date__isnull=True,
    )

    source_shelf = assignment.shelf
    item = assignment.item

    if request.method == 'POST':
        # Process form submission - get the target shelf ID
        target_shelf_id = request.POST.get('shelf')

        if not target_shelf_id:
            messages.error(request, 'Proszę wybrać półkę docelową.')
            # Get all rooms to repopulate the form
            rooms = Room.objects.all().order_by('name')
            return render(
                request,
                'warehouse/move_items.html',
                {
                    'rooms': rooms,
                    'source_shelf': source_shelf,
                    'item_name': item.name,
                    'category': item.category,
                    'manufacturer': item.manufacturer,
                    'expiration_date': item.expiration_date,
                    'items_count': 1,
                    'assignment': assignment,
                },
            )

        # Don't allow moving to the same shelf
        if int(target_shelf_id) == source_shelf.id:
            messages.error(request, 'Nie można przenieść przedmiotu na tę samą półkę.')
            rooms = Room.objects.all().order_by('name')
            return render(
                request,
                'warehouse/move_items.html',
                {
                    'rooms': rooms,
                    'source_shelf': source_shelf,
                    'item_name': item.name,
                    'category': item.category,
                    'manufacturer': item.manufacturer,
                    'expiration_date': item.expiration_date,
                    'items_count': 1,
                    'assignment': assignment,
                },
            )

        # Move the item
        success, message, new_assignment = move_item_between_shelves(
            item_id=item.id,
            from_shelf_id=source_shelf.id,
            to_shelf_id=target_shelf_id,
            user=request.user,
        )

        if success:
            target_shelf = get_object_or_404(Shelf, pk=target_shelf_id)
            messages.success(
                request,
                f'Przedmiot "{item.name}" został pomyślnie przeniesiony na półkę {target_shelf.full_location}.',
            )
            return redirect('warehouse:shelf_detail', pk=target_shelf_id)
        else:
            messages.error(request, f'Błąd podczas przenoszenia przedmiotu: {message}')
            return redirect('warehouse:shelf_detail', pk=source_shelf.id)

    # GET request - show the form to select target location
    rooms = Room.objects.all().order_by('name')

    return render(
        request,
        'warehouse/move_items.html',
        {
            'rooms': rooms,
            'source_shelf': source_shelf,
            'item_name': item.name,
            'category': item.category,
            'manufacturer': item.manufacturer,
            'expiration_date': item.expiration_date,
            'items_count': 1,
            'assignment': assignment,
        },
    )
