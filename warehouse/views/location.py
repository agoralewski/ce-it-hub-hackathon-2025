"""
Location management views for rooms, racks, and shelves.
"""
from datetime import timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse
from django.db import IntegrityError, transaction
from django.core.paginator import Paginator
from django.utils import timezone

from warehouse.models import Room, Rack, Shelf, ItemShelfAssignment
from warehouse.forms import RoomForm, RackForm, ShelfForm
from warehouse.views.utils import is_admin


def move_item_between_shelves(item_id, from_shelf_id, to_shelf_id, user):
    """
    Move an item from one shelf to another by ending the old assignment and creating a new one.
    
    Args:
        item_id (int): ID of the item to move
        from_shelf_id (int): ID of the shelf the item is currently on
        to_shelf_id (int): ID of the shelf to move the item to
        user (User): The user performing the move
    
    Returns:
        tuple: (bool, str, ItemShelfAssignment) - Success status, message, and the new assignment if successful
    """
    try:
        with transaction.atomic():
            # Find the active assignment for this item on the source shelf
            assignment = ItemShelfAssignment.objects.get(
                item_id=item_id,
                shelf_id=from_shelf_id,
                remove_date__isnull=True
            )
            
            # Mark the old assignment as removed
            assignment.remove_date = timezone.now()
            assignment.removed_by = user
            assignment.save()
            
            # Create a new assignment for the same item on the destination shelf
            new_assignment = ItemShelfAssignment.objects.create(
                item_id=item_id,
                shelf_id=to_shelf_id,
                added_by=user
            )
            
            return True, f"Item {assignment.item.name} moved successfully", new_assignment
    except ItemShelfAssignment.DoesNotExist:
        return False, "No active assignment found for this item on the source shelf", None
    except Exception as e:
        return False, f"Error moving item: {str(e)}", None


def batch_move_items_between_shelves(item_ids, from_shelf_id, to_shelf_id, user):
    """
    Move multiple items from one shelf to another in a single transaction.
    This is more efficient than calling move_item_between_shelves multiple times.
    
    Args:
        item_ids (list): List of item IDs to move
        from_shelf_id (int): ID of the shelf the items are currently on
        to_shelf_id (int): ID of the shelf to move the items to
        user (User): The user performing the move
    
    Returns:
        tuple: (int, list, list) - Count of successfully moved items, list of new assignments, list of errors
    """
    if not item_ids:
        return 0, [], []
    
    successfully_moved = 0
    new_assignments = []
    errors = []
    
    try:
        with transaction.atomic():
            # Find all active assignments for these items on the source shelf
            active_assignments = ItemShelfAssignment.objects.filter(
                item_id__in=item_ids,
                shelf_id=from_shelf_id,
                remove_date__isnull=True
            ).select_related('item')
            
            # Check if we found all requested items
            found_item_ids = set(assignment.item_id for assignment in active_assignments)
            missing_item_ids = set(item_ids) - found_item_ids
            
            if missing_item_ids:
                errors.append(f"Could not find {len(missing_item_ids)} items on the source shelf")
            
            # Mark all old assignments as removed
            now = timezone.now()
            for assignment in active_assignments:
                assignment.remove_date = now
                assignment.removed_by = user
            
            # Bulk update the removed assignments
            if active_assignments:
                ItemShelfAssignment.objects.bulk_update(
                    active_assignments, ['remove_date', 'removed_by']
                )
            
            # Create new assignments for all items
            new_assignments_to_create = [
                ItemShelfAssignment(
                    item_id=assignment.item_id,
                    shelf_id=to_shelf_id,
                    added_by=user
                )
                for assignment in active_assignments
            ]
            
            # Bulk create the new assignments
            if new_assignments_to_create:
                created_assignments = ItemShelfAssignment.objects.bulk_create(new_assignments_to_create)
                new_assignments = created_assignments
                successfully_moved = len(created_assignments)
            
            return successfully_moved, new_assignments, errors
    except Exception as e:
        return 0, [], [str(e)]


# Room management views
@login_required
@user_passes_test(is_admin)
def room_list(request):
    """List of all rooms with their racks and shelves"""
    rooms = (
        Room.objects.all().order_by('name').prefetch_related('racks', 'racks__shelves')
    )
    return render(request, 'warehouse/room_list.html', {'rooms': rooms})


@login_required
@user_passes_test(is_admin)
def room_create(request):
    """Create a new room"""
    if request.method == 'POST':
        form = RoomForm(request.POST)
        if form.is_valid():
            try:
                room = form.save()
                messages.success(request, 'Pokój został pomyślnie utworzony.')
                return redirect(f'{reverse("warehouse:room_list")}?new_room={room.id}')
            except IntegrityError:
                messages.error(request, 'Pokój o tej nazwie już istnieje.')
    else:
        form = RoomForm()

    return render(
        request, 'warehouse/room_form.html', {'form': form, 'title': 'Create Room'}
    )


@login_required
@user_passes_test(is_admin)
def room_update(request, pk):
    """Update an existing room"""
    room = get_object_or_404(Room, pk=pk)

    if request.method == 'POST':
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            messages.success(request, 'Pokój został pomyślnie zaktualizowany.')
            return redirect('warehouse:room_list')
    else:
        form = RoomForm(instance=room)

    return render(
        request, 'warehouse/room_form.html', {'form': form, 'title': 'Update Room'}
    )


@login_required
@user_passes_test(is_admin)
def room_delete(request, pk):
    """Delete a room"""
    room = get_object_or_404(Room, pk=pk)

    # Check if room has any items
    has_items = ItemShelfAssignment.objects.filter(
        shelf__rack__room=room, remove_date__isnull=True
    ).exists()

    if request.method == 'POST':
        if 'confirm' in request.POST:
            room.delete()
            messages.success(request, 'Pokój został pomyślnie usunięty.')
            return redirect('warehouse:room_list')

    return render(
        request, 'warehouse/room_delete.html', {'room': room, 'has_items': has_items}
    )


@login_required
@user_passes_test(is_admin)
def clean_room(request, pk):
    """Move all items from a room to an 'Unassigned' room with rack A and shelf 1"""
    room = get_object_or_404(Room, pk=pk)
    
    # Check if room has any items
    active_assignments = ItemShelfAssignment.objects.filter(
        shelf__rack__room=room, remove_date__isnull=True
    ).select_related('item', 'shelf', 'shelf__rack')
    
    items_count = active_assignments.count()
    
    if request.method == 'POST' and 'confirm' in request.POST and items_count > 0:
        with transaction.atomic():
            # Ensure the "Unassigned" room exists
            unassigned_room, _ = Room.objects.get_or_create(
                name="Unassigned",
                defaults={"name": "Unassigned"}
            )
            
            # Ensure rack "A" exists in the unassigned room
            unassigned_rack, _ = Rack.objects.get_or_create(
                name="A", 
                room=unassigned_room,
                defaults={"name": "A", "room": unassigned_room}
            )
            
            # Ensure shelf "1" exists in the unassigned rack
            unassigned_shelf, _ = Shelf.objects.get_or_create(
                number=1, 
                rack=unassigned_rack,
                defaults={"number": 1, "rack": unassigned_rack}
            )
            
            # Group items by source shelf for batch processing
            shelf_to_items = {}
            for assignment in active_assignments:
                if assignment.shelf_id not in shelf_to_items:
                    shelf_to_items[assignment.shelf_id] = []
                shelf_to_items[assignment.shelf_id].append(assignment.item_id)
            
            # Move all items from this room to the unassigned shelf using batch processing
            moved_count = 0
            new_assignments = []
            errors = []
            
            for source_shelf_id, item_ids in shelf_to_items.items():
                batch_moved, batch_assignments, batch_errors = batch_move_items_between_shelves(
                    item_ids=item_ids,
                    from_shelf_id=source_shelf_id,
                    to_shelf_id=unassigned_shelf.id,
                    user=request.user
                )
                moved_count += batch_moved
                new_assignments.extend(batch_assignments)
                errors.extend(batch_errors)
            
            messages.success(
                request, 
                f'Pokój "{room.name}" został wyczyszczony. {moved_count} przedmiotów zostało przeniesionych do lokalizacji "Unassigned.A.1".'
            )
            return redirect('warehouse:room_list')
    
    return render(
        request, 
        'warehouse/room_clean.html', 
        {
            'room': room, 
            'has_items': items_count > 0,
            'items_count': items_count
        }
    )


# Rack management views
@login_required
@user_passes_test(is_admin)
def rack_create(request, room_id):
    """Create a new rack in a room"""
    room = get_object_or_404(Room, pk=room_id)

    if request.method == 'POST':
        form = RackForm(request.POST, room=room)  # Pass room to the form
        if form.is_valid():
            rack = form.save(commit=False)
            rack.room = room  # Explicitly set the room
            rack.save()
            messages.success(request, 'Regał został pomyślnie utworzony.')
            return redirect(f'{reverse("warehouse:room_list")}?new_room={room.id}')
    else:
        form = RackForm(room=room)  # Pass room to the form

    return render(
        request,
        'warehouse/rack_form.html',
        {'form': form, 'room': room, 'title': 'Create Rack'},
    )


@login_required
@user_passes_test(is_admin)
def rack_update(request, pk):
    """Update an existing rack"""
    rack = get_object_or_404(Rack, pk=pk)

    if request.method == 'POST':
        form = RackForm(request.POST, instance=rack)
        if form.is_valid():
            form.save()
            messages.success(request, 'Regał został pomyślnie zaktualizowany.')
            return redirect('warehouse:room_list')
    else:
        form = RackForm(instance=rack)

    return render(
        request,
        'warehouse/rack_form.html',
        {'form': form, 'room': rack.room, 'title': 'Update Rack'},
    )


@login_required
@user_passes_test(is_admin)
def rack_delete(request, pk):
    """Delete a rack"""
    rack = get_object_or_404(Rack, pk=pk)

    # Check if rack has any items
    has_items = ItemShelfAssignment.objects.filter(
        shelf__rack=rack, remove_date__isnull=True
    ).exists()

    if request.method == 'POST':
        if 'confirm' in request.POST:
            rack.delete()
            messages.success(request, 'Regał został pomyślnie usunięty.')
            return redirect('warehouse:room_list')

    return render(
        request, 'warehouse/rack_delete.html', {'rack': rack, 'has_items': has_items}
    )


# Shelf management views
@login_required
@user_passes_test(is_admin)
def shelf_create(request, rack_id):
    """Create a new shelf in a rack"""
    rack = get_object_or_404(Rack, pk=rack_id)

    if request.method == 'POST':
        form = ShelfForm(request.POST, rack=rack)  # Pass rack to the form
        if form.is_valid():
            shelf = form.save(commit=False)
            shelf.rack = rack  # Explicitly set the rack
            shelf.save()
            messages.success(request, 'Półka została pomyślnie utworzona.')
            return redirect('warehouse:shelf_detail', pk=shelf.pk)
    else:
        form = ShelfForm(rack=rack)  # Pass rack to the form

    return render(
        request,
        'warehouse/shelf_form.html',
        {'form': form, 'rack': rack, 'title': 'Create Shelf'},
    )


@login_required
@user_passes_test(is_admin)
def shelf_update(request, pk):
    """Update an existing shelf"""
    shelf = get_object_or_404(Shelf, pk=pk)

    if request.method == 'POST':
        form = ShelfForm(request.POST, instance=shelf)
        if form.is_valid():
            form.save()
            messages.success(request, 'Półka została pomyślnie zaktualizowana.')
            return redirect('warehouse:room_list')
    else:
        form = ShelfForm(instance=shelf)

    return render(
        request,
        'warehouse/shelf_form.html',
        {'form': form, 'rack': shelf.rack, 'title': 'Update Shelf'},
    )


@login_required
@user_passes_test(is_admin)
def shelf_delete(request, pk):
    """Delete a shelf"""
    shelf = get_object_or_404(Shelf, pk=pk)

    # Check if shelf has any items
    has_items = ItemShelfAssignment.objects.filter(
        shelf=shelf, remove_date__isnull=True
    ).exists()

    if request.method == 'POST':
        if 'confirm' in request.POST:
            shelf.delete()
            messages.success(request, 'Półka została pomyślnie usunięta.')
            return redirect('warehouse:room_list')

    return render(
        request, 'warehouse/shelf_delete.html', {'shelf': shelf, 'has_items': has_items}
    )


@login_required
def shelf_detail(request, pk):
    """Detail view of a shelf with its items"""
    shelf = get_object_or_404(Shelf.objects.select_related('rack', 'rack__room'), pk=pk)

    # Get active assignments with optimized related fields
    assignments = ItemShelfAssignment.objects.filter(
        shelf=shelf, remove_date__isnull=True
    ).select_related('item', 'item__category', 'added_by')

    # Add pagination to handle large number of items on a shelf
    paginator = Paginator(assignments, 50)  # Show 50 items per page
    page_number = request.GET.get('page')
    assignments_page = paginator.get_page(page_number)

    # Add date context for expiration highlighting
    today_date = timezone.now().date()
    thirty_days_from_now = today_date + timedelta(days=30)

    # Create a network-aware absolute URL for this shelf
    from django.urls import reverse
    from warehouse.views.utils import build_network_absolute_uri
    shelf_url = build_network_absolute_uri(request, reverse('warehouse:shelf_detail', kwargs={'pk': shelf.pk}))

    return render(
        request,
        'warehouse/shelf_detail.html',
        {
            'shelf': shelf,
            'assignments': assignments_page,
            'page_obj': assignments_page,
            'total_count': assignments.count(),
            'today_date': today_date,
            'thirty_days_from_now': thirty_days_from_now,
            'shelf_url': shelf_url,  # Add the network-aware URL to the context
        },
    )


@login_required
def move_items_to_shelf(request, shelf_id):
    """Move items from one shelf to another"""
    target_shelf = get_object_or_404(Shelf.objects.select_related('rack', 'rack__room'), pk=shelf_id)
    
    if request.method == 'POST':
        # Get the source shelf ID
        source_shelf_id = request.POST.get('source_shelf')
        if not source_shelf_id:
            messages.error(request, 'Należy wybrać półkę źródłową.')
            return redirect('warehouse:shelf_detail', pk=shelf_id)
            
        # Get the items to move (their IDs)
        item_ids = request.POST.getlist('item_ids')
        if not item_ids:
            messages.error(request, 'Nie wybrano przedmiotów do przeniesienia.')
            return redirect('warehouse:shelf_detail', pk=shelf_id)
        
        # Process the move using batch function for better performance
        with transaction.atomic():
            moved_count, new_assignments, errors = batch_move_items_between_shelves(
                item_ids=item_ids,
                from_shelf_id=source_shelf_id, 
                to_shelf_id=shelf_id,
                user=request.user
            )
            
            # Display any errors
            for error in errors:
                messages.warning(request, error)
            
            successfully_moved = moved_count
        
        if successfully_moved > 0:
            messages.success(
                request, 
                f'{successfully_moved} przedmiot(ów) zostało pomyślnie przeniesionych na półkę {target_shelf.full_location}.'
            )
        else:
            messages.warning(request, 'Nie udało się przenieść żadnych przedmiotów.')
            
        return redirect('warehouse:shelf_detail', pk=shelf_id)
    
    # If GET request, show a form to select source shelf and items
    # Get all rooms, racks and shelves to populate the dropdowns
    rooms = Room.objects.all().order_by('name')
    
    return render(
        request, 
        'warehouse/move_items.html', 
        {
            'target_shelf': target_shelf,
            'rooms': rooms,
        }
    )


@login_required
@user_passes_test(is_admin)
def clean_rack(request, pk):
    """Move all items from a rack to an 'Unassigned' room with rack A and shelf 1"""
    rack = get_object_or_404(Rack.objects.select_related('room'), pk=pk)
    
    # Check if rack has any items
    active_assignments = ItemShelfAssignment.objects.filter(
        shelf__rack=rack, remove_date__isnull=True
    ).select_related('item', 'shelf')
    
    items_count = active_assignments.count()
    
    if request.method == 'POST' and 'confirm' in request.POST and items_count > 0:
        with transaction.atomic():
            # Ensure the "Unassigned" room exists
            unassigned_room, _ = Room.objects.get_or_create(
                name="Unassigned",
                defaults={"name": "Unassigned"}
            )
            
            # Ensure rack "A" exists in the unassigned room
            unassigned_rack, _ = Rack.objects.get_or_create(
                name="A", 
                room=unassigned_room,
                defaults={"name": "A", "room": unassigned_room}
            )
            
            # Ensure shelf "1" exists in the unassigned rack
            unassigned_shelf, _ = Shelf.objects.get_or_create(
                number=1, 
                rack=unassigned_rack,
                defaults={"number": 1, "rack": unassigned_rack}
            )
            
            # Group items by source shelf for batch processing
            shelf_to_items = {}
            for assignment in active_assignments:
                if assignment.shelf_id not in shelf_to_items:
                    shelf_to_items[assignment.shelf_id] = []
                shelf_to_items[assignment.shelf_id].append(assignment.item_id)
            
            # Move all items from this rack to the unassigned shelf using batch processing
            moved_count = 0
            new_assignments = []
            errors = []
            
            for source_shelf_id, item_ids in shelf_to_items.items():
                batch_moved, batch_assignments, batch_errors = batch_move_items_between_shelves(
                    item_ids=item_ids,
                    from_shelf_id=source_shelf_id,
                    to_shelf_id=unassigned_shelf.id,
                    user=request.user
                )
                moved_count += batch_moved
                new_assignments.extend(batch_assignments)
                errors.extend(batch_errors)
            
            messages.success(
                request, 
                f'Regał "{rack.room.name}.{rack.name}" został wyczyszczony. {moved_count} przedmiotów zostało przeniesionych do lokalizacji "Unassigned.A.1".'
            )
            return redirect('warehouse:room_list')
    
    return render(
        request, 
        'warehouse/rack_clean.html', 
        {
            'rack': rack,
            'has_items': items_count > 0,
            'items_count': items_count
        }
    )


@login_required
@user_passes_test(is_admin)
def clean_shelf(request, pk):
    """Move all items from a shelf to an 'Unassigned' room with rack A and shelf 1"""
    shelf = get_object_or_404(Shelf.objects.select_related('rack', 'rack__room'), pk=pk)
    
    # Check if shelf has any items
    active_assignments = ItemShelfAssignment.objects.filter(
        shelf=shelf, remove_date__isnull=True
    ).select_related('item')
    
    items_count = active_assignments.count()
    
    if request.method == 'POST' and 'confirm' in request.POST and items_count > 0:
        with transaction.atomic():
            # Ensure the "Unassigned" room exists
            unassigned_room, _ = Room.objects.get_or_create(
                name="Unassigned",
                defaults={"name": "Unassigned"}
            )
            
            # Ensure rack "A" exists in the unassigned room
            unassigned_rack, _ = Rack.objects.get_or_create(
                name="A", 
                room=unassigned_room,
                defaults={"name": "A", "room": unassigned_room}
            )
            
            # Ensure shelf "1" exists in the unassigned rack
            unassigned_shelf, _ = Shelf.objects.get_or_create(
                number=1, 
                rack=unassigned_rack,
                defaults={"number": 1, "rack": unassigned_rack}
            )
            
            # Get all item IDs from this shelf
            item_ids = [assignment.item_id for assignment in active_assignments]
            
            # Move all items from this shelf to the unassigned shelf
            moved_count, new_assignments, errors = batch_move_items_between_shelves(
                item_ids=item_ids,
                from_shelf_id=shelf.id,
                to_shelf_id=unassigned_shelf.id,
                user=request.user
            )
            
            messages.success(
                request, 
                f'Półka "{shelf.rack.room.name}.{shelf.rack.name}.{shelf.number}" została wyczyszczona. {moved_count} przedmiotów zostało przeniesionych do lokalizacji "Unassigned.A.1".'
            )
            return redirect('warehouse:shelf_detail', pk=shelf.id)
    
    return render(
        request, 
        'warehouse/shelf_clean.html', 
        {
            'shelf': shelf,
            'has_items': items_count > 0,
            'items_count': items_count
        }
    )