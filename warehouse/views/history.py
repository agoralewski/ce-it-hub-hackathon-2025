"""
History views for tracking item additions and removals.
"""


from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q, Case, When, DateTimeField, F
from django.utils import timezone
from django.core.paginator import Paginator

from warehouse.models import ItemShelfAssignment
from warehouse.views.utils import is_admin


@login_required
@user_passes_test(is_admin)
def history_list(request):
    """List view of all item additions and removals"""
    # Get filter parameters
    room_id = request.GET.get('room')
    rack_id = request.GET.get('rack')
    shelf_id = request.GET.get('shelf')
    username = request.GET.get('username')
    item_search = request.GET.get('search')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    action_type = request.GET.get('action_type')  # 'add' or 'remove'

    # Base queryset with all related data to minimize database hits
    assignments = ItemShelfAssignment.objects.select_related(
        'item',
        'shelf',
        'shelf__rack',
        'shelf__rack__room',
        'item__category',
        'added_by',
        'removed_by',
    )

    # Apply filters if provided
    if room_id:
        assignments = assignments.filter(shelf__rack__room_id=room_id)
    if rack_id:
        assignments = assignments.filter(shelf__rack_id=rack_id)
    if shelf_id:
        assignments = assignments.filter(shelf_id=shelf_id)
    if username:
        # Filter by either added_by or removed_by username
        assignments = assignments.filter(
            Q(added_by__username__icontains=username)
            | Q(removed_by__username__icontains=username)
        )
    if item_search:
        # Filter by item name
        assignments = assignments.filter(item__name__icontains=item_search)

    # Filter by date ranges if provided
    if date_from:
        try:
            # Convert from string to date object
            from_date = timezone.datetime.strptime(date_from, '%Y-%m-%d').date()
            # Add timezone info and set to start of day
            from_datetime = timezone.datetime.combine(
                from_date, timezone.datetime.min.time()
            )
            from_datetime = timezone.make_aware(from_datetime)

            # Filter additions and removals that happened after this date
            assignments = assignments.filter(
                Q(add_date__gte=from_datetime) | Q(remove_date__gte=from_datetime)
            )
        except (ValueError, TypeError):
            pass  # Invalid date format, ignore filter

    if date_to:
        try:
            # Convert from string to date object
            to_date = timezone.datetime.strptime(date_to, '%Y-%m-%d').date()
            # Add timezone info and set to end of day
            to_datetime = timezone.datetime.combine(
                to_date, timezone.datetime.max.time()
            )
            to_datetime = timezone.make_aware(to_datetime)

            # Filter additions and removals that happened before this date
            assignments = assignments.filter(
                Q(add_date__lte=to_datetime)
                & (Q(remove_date__lte=to_datetime) | Q(remove_date__isnull=True))
            )
        except (ValueError, TypeError):
            pass  # Invalid date format, ignore filter

    # Filter by action type if provided
    if action_type == 'add':
        # Only show additions (not removed)
        assignments = assignments.filter(remove_date__isnull=True)
        # Sort by most recent additions first
        assignments = assignments.order_by('-add_date')
    elif action_type == 'remove':
        # Only show removals (filter for non-null remove_date)
        assignments = assignments.filter(remove_date__isnull=False)
        # Sort by most recent removals first
        assignments = assignments.order_by('-remove_date')
    else:
        # Show all actions (both additions and removals)
        # Annotate with the latest operation date (remove_date if exists, else add_date)
        assignments = assignments.annotate(
            latest_operation=Case(
                When(remove_date__isnull=False, then=F('remove_date')),
                default=F('add_date'),
                output_field=DateTimeField(),
            )
        ).order_by('-latest_operation')

    # Get total count for stats (before pagination)
    total_count = assignments.count()

    # Add pagination
    paginator = Paginator(assignments, 50)  # Show 50 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get all rooms for filter dropdown (for consistent UI with other list views)
    from warehouse.models import Room, Rack, Shelf

    rooms = Room.objects.all()

    # Get racks filtered by room if needed
    racks = Rack.objects.all()
    if room_id:
        racks = racks.filter(room_id=room_id)

    # Get shelves filtered by rack or room if needed
    shelves = Shelf.objects.all()
    if rack_id:
        shelves = shelves.filter(rack_id=rack_id)
    elif room_id:
        shelves = shelves.filter(rack__room_id=room_id)

    return render(
        request,
        'warehouse/history_list.html',
        {
            'assignments': page_obj,
            'page_obj': page_obj,
            'total_count': total_count,
            'rooms': rooms,
            'racks': racks,
            'shelves': shelves,
            'selected_room': room_id,
            'selected_rack': rack_id,
            'selected_shelf': shelf_id,
            'username': username,
            'search_query': item_search,
            'date_from': date_from,
            'date_to': date_to,
            'action_type': action_type,
        },
    )
