"""
Core views for the warehouse app.
"""
from datetime import timedelta

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from django.core.paginator import Paginator
from django.urls import reverse

from warehouse.models import Room, ItemShelfAssignment, Rack, Shelf, Category


@login_required
def index(request):
    """Dashboard view"""
    rooms = (
        Room.objects.all()
        .annotate(
            rack_count=Count('racks', distinct=True),
            shelf_count=Count('racks__shelves', distinct=True),
            active_items=Count(
                'racks__shelves__assignments',
                filter=Q(racks__shelves__assignments__remove_date__isnull=True),
            ),
        )
        .order_by('name')
    )  # Sort alphabetically by room name

    return render(
        request,
        'warehouse/index.html',
        {'rooms': rooms},
    )


@login_required
def item_list(request):
    """List of all active items in warehouse"""
    # Get filter parameters
    room_id = request.GET.get('room')
    rack_id = request.GET.get('rack')
    shelf_id = request.GET.get('shelf')
    category_id = request.GET.get('category')
    search_query = request.GET.get('search')
    filter_values = request.GET.getlist('filter')  # Get all filter values as a list
    has_note = request.GET.get('has_note')

    # Use select_related to fetch related objects in a single query
    assignments = ItemShelfAssignment.objects.filter(
        remove_date__isnull=True
    ).select_related(
        'item',
        'shelf',
        'shelf__rack',
        'shelf__rack__room',
        'item__category',
        'added_by',
    )

    # Apply filters if provided
    if room_id:
        assignments = assignments.filter(shelf__rack__room_id=room_id)
    if rack_id:
        assignments = assignments.filter(shelf__rack_id=rack_id)
    if shelf_id:
        assignments = assignments.filter(shelf_id=shelf_id)
    if category_id:
        assignments = assignments.filter(item__category_id=category_id)

    # Apply search filter if provided
    if search_query:
        assignments = assignments.filter(item__name__icontains=search_query)

    # Apply 'has_note' filter if provided
    if has_note:
        assignments = assignments.filter(item__note__isnull=False).exclude(
            item__note=''
        )

    # Create a Q object to collect multiple filter conditions
    filters_q = Q()

    # Apply 'expiring_soon' filter if provided
    if 'expiring_soon' in filter_values:
        expiring_soon_q = Q(
            item__expiration_date__isnull=False,
            item__expiration_date__lte=timezone.now().date() + timedelta(days=30),
            item__expiration_date__gte=timezone.now().date(),  # Exclude expired items
        )
        filters_q |= expiring_soon_q

    # Apply 'expired' filter if provided
    if 'expired' in filter_values:
        expired_q = Q(
            item__expiration_date__isnull=False,
            item__expiration_date__lt=timezone.now().date(),
        )
        filters_q |= expired_q

    # Apply combined filters if any were selected
    if filter_values:
        assignments = assignments.filter(filters_q)

    # Get total count for stats (before pagination)
    total_count = assignments.count()

    # Add pagination
    paginator = Paginator(assignments, 100)  # Show 100 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get filter options
    rooms = Room.objects.all()
    racks = Rack.objects.all()
    if room_id:
        racks = racks.filter(room_id=room_id)

    shelves = Shelf.objects.all()
    if rack_id:
        shelves = shelves.filter(rack_id=rack_id)
    elif room_id:
        # Also filter shelves by room when only room is selected
        shelves = shelves.filter(rack__room_id=room_id)

    categories = Category.objects.all()

    today_date = timezone.now().date()
    thirty_days_from_now = today_date + timedelta(days=30)

    return render(
        request,
        'warehouse/item_list.html',
        {
            'assignments': page_obj,  # Use paginated assignments
            'page_obj': page_obj,  # Add page object for pagination controls
            'total_count': total_count,
            'rooms': rooms,
            'racks': racks,
            'shelves': shelves,
            'categories': categories,
            'selected_room': room_id,
            'selected_rack': rack_id,
            'selected_shelf': shelf_id,
            'selected_category': category_id,
            'search_query': search_query,
            'filter_values': filter_values,
            'has_note': has_note,
            'today_date': today_date,
            'thirty_days_from_now': thirty_days_from_now,
        },
    )


@login_required
def low_stock(request):
    """View for categories with low stock"""
    # Use a more efficient query with prefetch_related to reduce database hits
    categories = (
        Category.objects.annotate(
            active_items=Count(
                'items__assignments',
                filter=Q(items__assignments__remove_date__isnull=True),
            )
        )
        .filter(active_items__lt=10)
        .prefetch_related('items__assignments__shelf__rack__room')
    )

    low_stock_categories = []
    for category in categories:
        # Use optimized query that leverages the prefetched data
        assignments = [
            a
            for item in category.items.all()
            for a in item.assignments.all()
            if a.remove_date is None
        ]

        # Deduplicate shelves by their id
        seen_shelf_ids = set()
        location_data = []

        for assignment in assignments:
            shelf_id = assignment.shelf.id
            if shelf_id not in seen_shelf_ids:
                seen_shelf_ids.add(shelf_id)
                location_data.append(
                    {
                        'id': shelf_id,
                        'full_location': assignment.shelf.full_location,
                        'path': reverse(
                            'warehouse:shelf_detail', kwargs={'pk': shelf_id}
                        ),
                    }
                )

        low_stock_categories.append(
            {
                'name': category.name,
                'active_items': category.active_items,
                'locations': location_data,
            }
        )

    return render(
        request,
        'warehouse/low_stock.html',
        {'low_stock_categories': low_stock_categories},
    )