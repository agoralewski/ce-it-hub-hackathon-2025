"""
AJAX views for dynamic filtering and autocomplete.
"""

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

from warehouse.models import (
    Category,
    Rack,
    Shelf,
    Item,
    ItemShelfAssignment,
)


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
    # Accept both 'room' and 'room_id' parameter names for backwards compatibility
    room_id = request.GET.get('room_id') or request.GET.get('room')

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
    # Accept both 'rack' and 'rack_id' parameter names for backwards compatibility
    rack_id = request.GET.get('rack_id') or request.GET.get('rack')
    # Accept both 'room' and 'room_id' parameter names for backwards compatibility
    room_id = request.GET.get('room_id') or request.GET.get('room')

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


@login_required
def autocomplete_users(request):
    """AJAX view for user autocomplete"""
    from django.contrib.auth.models import User

    query = request.GET.get('term', '')

    if query:
        # If there's a search query, filter and limit results
        users = User.objects.filter(username__icontains=query)[:10]

        # Format results with username and email
        results = [
            {'id': user.username, 'text': f'{user.username} ({user.email})'}
            for user in users
        ]
    else:
        # For empty queries, don't return anything to avoid loading the entire dataset
        results = []

    return JsonResponse({'results': results})


@login_required
def get_shelf_items(request):
    """AJAX view for getting items on a shelf"""
    shelf_id = request.GET.get('shelf_id')

    if not shelf_id:
        return JsonResponse([], safe=False)

    # Get active items on this shelf with their details
    items_on_shelf = ItemShelfAssignment.objects.filter(
        shelf_id=shelf_id, remove_date__isnull=True
    ).select_related('item', 'item__category')

    items_data = [
        {
            'id': assignment.item.id,
            'name': assignment.item.name,
            'category': assignment.item.category.name
            if assignment.item.category
            else None,
            'manufacturer': assignment.item.manufacturer,
            'expiration_date': assignment.item.expiration_date.strftime('%Y-%m-%d')
            if assignment.item.expiration_date
            else None,
            'assignment_id': assignment.id,
        }
        for assignment in items_on_shelf
    ]

    return JsonResponse(items_data, safe=False)


@login_required
def get_rack_info(request):
    """AJAX view to get parent room for a given rack"""
    rack_id = request.GET.get('rack_id')
    try:
        rack = Rack.objects.select_related('room').get(pk=rack_id)
        return JsonResponse({'room_id': rack.room.id, 'room_name': rack.room.name})
    except Rack.DoesNotExist:
        return JsonResponse({'error': 'Rack not found'}, status=404)


@login_required
def get_shelf_info(request):
    """AJAX view to get parent rack and room for a given shelf"""
    shelf_id = request.GET.get('shelf_id')
    try:
        shelf = Shelf.objects.select_related('rack', 'rack__room').get(pk=shelf_id)
        return JsonResponse({
            'rack_id': shelf.rack.id,
            'rack_name': shelf.rack.name,
            'room_id': shelf.rack.room.id,
            'room_name': shelf.rack.room.name
        })
    except Shelf.DoesNotExist:
        return JsonResponse({'error': 'Shelf not found'}, status=404)
