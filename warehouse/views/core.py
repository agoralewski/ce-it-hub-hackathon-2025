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
    assignments = ItemShelfAssignment.objects.filter(
        remove_date__isnull=True
    ).select_related('item', 'shelf', 'shelf__rack', 'shelf__rack__room')

    # Apply filters if provided
    room_id = request.GET.get('room')
    rack_id = request.GET.get('rack')
    shelf_id = request.GET.get('shelf')
    category_id = request.GET.get('category')
    search_query = request.GET.get('search')
    filter_values = request.GET.getlist('filter')  # Get all filter values as a list
    has_note = request.GET.get('has_note')

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
        assignments = assignments.filter(item__note__isnull=False).exclude(item__note='')

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
    
    # Group assignments by item name, shelf, category and other properties using database aggregation
    from django.db.models import Count, F
    
    # We use values() to group by the relevant fields and annotate to count and collect assignments
    grouped_items_query = (
        assignments
        .values(
            'item__name',
            'shelf',
            'item__category',
            'item__manufacturer',
            'item__expiration_date',
            'item__note',
            'shelf__id',
            'item__category__id',
        )
        .annotate(
            item_name=F('item__name'),
            count=Count('id'),
            shelf_id=F('shelf__id'),
            category_id=F('item__category__id'),
            manufacturer=F('item__manufacturer'),
            expiration_date=F('item__expiration_date'),
            note=F('item__note'),
        )
    )
    
    # Fetch related objects in bulk to avoid N+1 queries
    shelf_ids = {item['shelf_id'] for item in grouped_items_query}
    shelves = {shelf.id: shelf for shelf in Shelf.objects.filter(id__in=shelf_ids).select_related('rack', 'rack__room')}
    
    category_ids = {item['category_id'] for item in grouped_items_query}
    categories = {category.id: category for category in Category.objects.filter(id__in=category_ids)}
    
    # Convert query results to the expected format for the template
    grouped_items = []
    for group in grouped_items_query:
        # Get the related objects from our prefetched dictionaries
        shelf = shelves.get(group['shelf_id'])
        category = categories.get(group['category_id'])
        
        # For each group, also fetch the actual assignment records
        group_assignments = assignments.filter(
            item__name=group['item_name'],
            shelf_id=group['shelf_id'],
            item__category_id=group['category_id'],
            item__manufacturer=group['manufacturer'],
            item__expiration_date=group['expiration_date'],
            item__note=group['note']
        )[:1]  # Limit to one assignment for display purposes
        
        grouped_items.append({
            'item_name': group['item_name'],
            'shelf': shelf,
            'category': category,
            'manufacturer': group['manufacturer'],
            'expiration_date': group['expiration_date'],
            'note': group['note'],
            'assignments': list(group_assignments),
            'count': group['count']
        })

    # Add pagination to handle large number of items
    paginator = Paginator(grouped_items, 50)  # Show 50 items per page
    page_number = request.GET.get('page')
    items_page = paginator.get_page(page_number)

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
            'assignments': assignments,  # Keep original for backward compatibility
            'grouped_items': items_page,  # Paginated grouped items for display
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
            'page_obj': items_page,  # Add page object for pagination controls
            'total_count': len(grouped_items),  # Add total count for info display
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