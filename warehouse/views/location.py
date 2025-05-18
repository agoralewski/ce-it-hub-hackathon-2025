"""
Location management views for rooms, racks, and shelves.
"""
from datetime import timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse
from django.db import IntegrityError
from django.core.paginator import Paginator
from django.utils import timezone

from warehouse.models import Room, Rack, Shelf, ItemShelfAssignment
from warehouse.forms import RoomForm, RackForm, ShelfForm
from warehouse.views.utils import is_admin


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
    """Detail view of a shelf with its items and summary stats"""
    shelf = get_object_or_404(Shelf.objects.select_related('rack', 'rack__room'), pk=pk)

    # Get active assignments with optimized related fields
    assignments = ItemShelfAssignment.objects.filter(
        shelf=shelf, remove_date__isnull=True
    ).select_related('item', 'item__category', 'added_by')

    # Expiration logic (same as item_list view)
    today_date = timezone.now().date()
    thirty_days_from_now = today_date + timedelta(days=30)

    expired_count = assignments.filter(
        item__expiration_date__isnull=False,
        item__expiration_date__lt=today_date
    ).count()
    nearly_expired_count = assignments.filter(
        item__expiration_date__isnull=False,
        item__expiration_date__gte=today_date,
        item__expiration_date__lte=thirty_days_from_now
    ).count()

    # Add pagination to handle large number of items on a shelf (not used in template, but kept for compatibility)
    paginator = Paginator(assignments, 50)
    page_number = request.GET.get('page')
    assignments_page = paginator.get_page(page_number)

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
            'expired_count': expired_count,
            'nearly_expired_count': nearly_expired_count,
            'today_date': today_date,
            'thirty_days_from_now': thirty_days_from_now,
            'shelf_url': shelf_url,
        },
    )