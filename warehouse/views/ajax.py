"""
AJAX views for dynamic filtering and autocomplete.
"""
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.urls import reverse

from warehouse.models import Category, Rack, Shelf, Item


@login_required
def autocomplete_categories(request):
    """AJAX view for category autocomplete"""
    query = request.GET.get('term', '')
    categories = Category.objects.filter(name__icontains=query)[:10]
    results = [{'id': c.id, 'text': c.name} for c in categories]
    return JsonResponse({'results': results})


@login_required
def get_racks(request):
    """AJAX view for getting racks by room"""
    room_id = request.GET.get('room')

    # Use select_related to reduce database queries
    racks = Rack.objects.select_related('room')

    if room_id:
        # Filter by room if specified
        racks = racks.filter(room_id=room_id)

    # Order by room name and then rack name for consistent display
    racks = racks.order_by('room__name', 'name')

    rack_data = [
        {'id': r.id, 'name': r.name, 'room_id': r.room.id, 'room_name': r.room.name}
        for r in racks
    ]

    return JsonResponse(rack_data, safe=False)


@login_required
def get_shelves(request):
    """AJAX view for getting shelves by rack"""
    rack_id = request.GET.get('rack')
    room_id = request.GET.get('room')

    # Start with all shelves, select_related to reduce db queries
    shelves = Shelf.objects.select_related('rack', 'rack__room')

    # Apply filters if provided
    if rack_id:
        shelves = shelves.filter(rack_id=rack_id)
    elif room_id:
        # If only room is provided, filter by room
        shelves = shelves.filter(rack__room_id=room_id)

    # Order by location for consistent display
    shelves = shelves.order_by('rack__room__name', 'rack__name', 'number')

    shelf_data = [
        {
            'id': s.id,
            'number': s.number,
            'rack_id': s.rack.id,
            'room_id': s.rack.room.id,
            'full_location': s.full_location,
        }
        for s in shelves
    ]

    return JsonResponse(shelf_data, safe=False)


@login_required
def autocomplete_items(request):
    """AJAX view for item name autocomplete"""
    query = request.GET.get('term', '')

    # Get distinct item names only, not full objects
    if query:
        # Filter by the query but only get distinct names
        # Using values_list with flat=True is more efficient than values() for simple name retrieval
        items = (
            Item.objects.filter(name__icontains=query)
            .values_list('name', flat=True)
            .distinct()[:10]
        )
        # Limit to 10 items for better performance on large datasets
    else:
        # For empty queries, return an empty list to avoid loading all items
        items = []

    # Format results with only name information
    results = [{'id': name, 'text': name} for name in items]

    return JsonResponse({'results': results})


@login_required
def autocomplete_manufacturers(request):
    """AJAX view for manufacturer autocomplete"""
    query = request.GET.get('term', '')

    # Use values_list with flat=True for better performance
    if query:
        # If there's a search query, filter and limit results
        manufacturers = (
            Item.objects.filter(
                manufacturer__isnull=False, manufacturer__icontains=query
            )
            .values_list('manufacturer', flat=True)
            .distinct()[:10]
        )
    else:
        # For empty queries, don't return anything to avoid loading the entire dataset
        manufacturers = []

    results = [{'id': m, 'text': m} for m in manufacturers]
    return JsonResponse({'results': results})