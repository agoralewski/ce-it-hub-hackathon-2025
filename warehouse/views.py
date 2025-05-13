import io
import xlsxwriter
from datetime import timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import update_session_auth_hash, logout
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db.models import Count, Q
from django.urls import reverse
from django.utils import timezone
from django.db import IntegrityError

from .models import Room, Rack, Shelf, Category, Item, ItemShelfAssignment
from .forms import (
    RoomForm,
    RackForm,
    ShelfForm,
    CategoryForm,
    ItemShelfAssignmentForm,
    ExportForm,
    CustomUserCreationForm,
)


def is_admin(user):
    """Check if user is a superuser (WH Administrator)"""
    return user.is_superuser


# Main views
@login_required
def index(request):
    """Dashboard view"""
    rooms = Room.objects.all().annotate(
        rack_count=Count('racks'),
        shelf_count=Count('racks__shelves'),
        active_items=Count(
            'racks__shelves__assignments',
            filter=Q(racks__shelves__assignments__remove_date__isnull=True),
        ),
    ).order_by('name')  # Sort alphabetically by room name

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
            'assignments': assignments,
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


# Room, rack, and shelf management (admin views)
@login_required
@user_passes_test(is_admin)
def room_list(request):
    """List of all rooms with their racks and shelves"""
    rooms = Room.objects.all().order_by('name').prefetch_related('racks', 'racks__shelves')
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


# Category management
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


# Shelf detail view and item management
@login_required
def shelf_detail(request, pk):
    """Detail view of a shelf with its items"""
    shelf = get_object_or_404(Shelf, pk=pk)

    # Get active assignments
    assignments = ItemShelfAssignment.objects.filter(
        shelf=shelf, remove_date__isnull=True
    ).select_related('item', 'item__category', 'added_by')

    # Add date context for expiration highlighting
    today_date = timezone.now().date()
    thirty_days_from_now = today_date + timedelta(days=30)

    return render(
        request,
        'warehouse/shelf_detail.html',
        {
            'shelf': shelf,
            'assignments': assignments,
            'today_date': today_date,
            'thirty_days_from_now': thirty_days_from_now,
        },
    )


@login_required
def add_item_to_shelf(request, shelf_id):
    """Add an item to a shelf"""
    shelf = get_object_or_404(Shelf, pk=shelf_id)

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

            # Create the specified number of items and assignments
            for _ in range(quantity):
                item = Item.objects.create(
                    name=item_name,
                    category=category,
                    manufacturer=manufacturer,
                    expiration_date=expiration_date,
                    note=note,
                )
                ItemShelfAssignment.objects.create(
                    item=item, shelf=shelf, added_by=request.user
                )

            messages.success(request, f'{quantity} przedmiot(ów) zostało dodanych na półkę.')
            return redirect('warehouse:shelf_detail', pk=shelf_id)
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
    context = {'form': form, 'shelf': shelf, 'input_data': {}}

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
        quantity = int(request.POST.get('quantity', 1))
        # Mark the assignment as removed
        assignment.remove_date = timezone.now()
        assignment.removed_by = request.user
        assignment.save()

        messages.success(request, 'Przedmiot został pomyślnie zdjęty z półki.')
        return redirect('warehouse:shelf_detail', pk=assignment.shelf.pk)

    return render(request, 'warehouse/remove_item.html', {'assignment': assignment})


# QR code generation
@login_required
@user_passes_test(is_admin)
def generate_qr_codes(request):
    """Generate QR codes for shelves"""
    shelves = Shelf.objects.all().select_related('rack', 'rack__room')

    if request.method == 'POST':
        selected_shelves = request.POST.getlist('shelves')

        if selected_shelves:
            # Create an in-memory PDF file with QR codes
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.units import mm
            from reportlab.platypus import SimpleDocTemplate
            import io

            # Get the selected shelves
            selected_shelves = Shelf.objects.filter(id__in=selected_shelves)

            # Create a BytesIO buffer to receive the PDF data
            buffer = io.BytesIO()

            # Create the PDF document
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            width, height = A4

            # Setup for 2x2 grid of QR codes per page
            qr_size = 80 * mm
            margin = 20 * mm
            spacing = 10 * mm

            # Create the canvas
            p = canvas.Canvas(buffer, pagesize=A4)

            # Generate QR codes for each shelf
            qr_per_page = 4  # 2x2 grid
            for i, shelf in enumerate(selected_shelves):
                if i > 0 and i % qr_per_page == 0:
                    # Start a new page after every 4 QR codes
                    p.showPage()

                # Calculate position for current QR code
                page_index = i % qr_per_page
                row = page_index // 2
                col = page_index % 2

                x = margin + col * (qr_size + spacing)
                y = height - (margin + qr_size) - row * (qr_size + spacing)

                # Generate QR code for the shelf's URL
                import qrcode

                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )

                # Make sure each shelf has a UUID
                if not shelf.qr_code_uuid:
                    shelf.save()  # This will trigger the UUID generation

                # Create the URL for the shelf detail page
                shelf_url = request.build_absolute_uri(
                    reverse('warehouse:shelf_detail', kwargs={'pk': shelf.pk})
                )

                qr.add_data(shelf_url)
                qr.make(fit=True)

                # Create an image from the QR Code instance
                img = qr.make_image(fill_color='black', back_color='white')

                # Create a temporary file for the image
                import tempfile

                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                temp_filename = temp_file.name

                # Save the image to the temporary file
                img.save(temp_filename)

                # Draw the QR code image on the canvas from the file
                p.drawImage(temp_filename, x, y, width=qr_size, height=qr_size)

                # Clean up the temporary file
                import os

                try:
                    os.unlink(temp_filename)
                except:
                    pass  # Ignore errors during cleanup

                # Draw shelf information below the QR code
                p.setFont('Helvetica', 12)
                p.drawString(x, y - 15, f'Location: {shelf.full_location}')
                p.drawString(x, y - 30, f'Shelf: {shelf}')

            # Save the PDF
            p.showPage()
            p.save()

            # Get the value of the BytesIO buffer
            pdf = buffer.getvalue()
            buffer.close()

            # Create the HTTP response with PDF content
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = (
                'attachment; filename="shelf_qr_codes.pdf"'
            )
            response.write(pdf)

            messages.success(request, 'Kody QR zostały pomyślnie wygenerowane.')
            return response

    return render(request, 'warehouse/generate_qr_codes.html', {'shelves': shelves})


# Excel export
@login_required
@user_passes_test(is_admin)
def export_inventory(request):
    """Export inventory to Excel"""
    rooms = Room.objects.all()
    racks = Rack.objects.all()
    shelves = Shelf.objects.all()
    categories = Category.objects.all()

    if request.method == 'POST':
        form = ExportForm(request.POST)

        if form.is_valid():
            # Get form data and ensure we have IDs, not objects
            room = form.cleaned_data.get('room')
            rack = form.cleaned_data.get('rack')
            shelf = form.cleaned_data.get('shelf')
            category = form.cleaned_data.get('category')
            
            # Extract IDs from model objects if present
            room_id = room.id if room else None
            rack_id = rack.id if rack else None
            shelf_id = shelf.id if shelf else None
            category_id = category.id if category else None
            
            include_expired = form.cleaned_data.get('include_expired', False)
            include_removed = form.cleaned_data.get('include_removed', False)

            # Build query based on form data
            query = Q()

            if not include_removed:
                query &= Q(remove_date__isnull=True)

            if shelf_id:
                query &= Q(shelf_id=shelf_id)
            elif rack_id:
                query &= Q(shelf__rack_id=rack_id)
            elif room_id:
                query &= Q(shelf__rack__room_id=room_id)

            if category_id:
                query &= Q(item__category_id=category_id)

            # Handle expiration filter
            if not include_expired:
                query &= Q(item__expiration_date__isnull=True) | Q(
                    item__expiration_date__gt=timezone.now().date()
                )

            assignments = ItemShelfAssignment.objects.filter(query).select_related(
                'item',
                'item__category',
                'shelf',
                'shelf__rack',
                'shelf__rack__room',
                'added_by',
                'removed_by',
            )

            # Create Excel file
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output, {'remove_timezone': True})

            # Add formatting
            header_format = workbook.add_format(
                {
                    'bold': True,
                    'bg_color': '#4a86e8',
                    'font_color': 'white',
                    'border': 1,
                }
            )

            date_format = workbook.add_format({'num_format': 'yyyy-mm-dd'})
            datetime_format = workbook.add_format({'num_format': 'yyyy-mm-dd hh:mm:ss'})
            expired_format = workbook.add_format({'bg_color': '#ffcccb', 'border': 1})
            removed_format = workbook.add_format(
                {'color': '#888888', 'italic': True, 'border': 1}
            )
            cell_format = workbook.add_format({'border': 1})

            # Create main inventory worksheet
            worksheet = workbook.add_worksheet('Inwentarz')
            worksheet.set_column('A:A', 25)  # Nazwa przedmiotu
            worksheet.set_column('B:B', 15)  # Kategoria
            worksheet.set_column('C:C', 15)  # Producent
            worksheet.set_column('D:D', 12)  # Data ważności
            worksheet.set_column('E:E', 20)  # Lokalizacja
            worksheet.set_column('F:G', 15)  # Dodany/Usunięty przez
            worksheet.set_column('H:I', 18)  # Data dodania/usunięcia
            worksheet.set_column('J:J', 25)  # Notatki

            # Add header with Polish names
            headers = [
                'Nazwa przedmiotu',
                'Kategoria',
                'Producent',
                'Data ważności',
                'Lokalizacja',
                'Dodany przez',
                'Data dodania',
                'Usunięty przez',
                'Data usunięcia',
                'Notatki',
            ]

            for col, header in enumerate(headers):
                worksheet.write(0, col, header, header_format)

            # Add data
            today = timezone.now().date()

            for row, assignment in enumerate(assignments, start=1):
                item = assignment.item

                # Determine if this item is expired
                is_expired = item.expiration_date and item.expiration_date < today
                is_removed = assignment.remove_date is not None

                # Use appropriate format based on item status
                current_format = cell_format
                if is_expired:
                    current_format = expired_format
                elif is_removed:
                    current_format = removed_format

                # Write the row data with appropriate formatting
                worksheet.write(row, 0, item.name, current_format)
                worksheet.write(row, 1, item.category.name, current_format)
                worksheet.write(row, 2, item.manufacturer or '', current_format)

                if item.expiration_date:
                    worksheet.write_datetime(row, 3, item.expiration_date, date_format)
                else:
                    worksheet.write(row, 3, '', current_format)

                worksheet.write(row, 4, assignment.shelf.full_location, current_format)
                worksheet.write(
                    row,
                    5,
                    assignment.added_by.username if assignment.added_by else 'System',
                    current_format,
                )
                worksheet.write_datetime(row, 6, assignment.add_date, datetime_format)

                if assignment.removed_by:
                    worksheet.write(
                        row, 7, assignment.removed_by.username, current_format
                    )
                else:
                    worksheet.write(row, 7, '', current_format)

                if assignment.remove_date:
                    worksheet.write_datetime(
                        row, 8, assignment.remove_date, datetime_format
                    )
                else:
                    worksheet.write(row, 8, '', current_format)

                worksheet.write(row, 9, item.note or '', current_format)

            # Create summary worksheet
            summary_sheet = workbook.add_worksheet('Podsumowanie')
            summary_sheet.set_column('A:A', 30)  # Opis
            summary_sheet.set_column('B:B', 15)  # Liczba

            title_format = workbook.add_format(
                {
                    'bold': True,
                    'font_size': 14,
                    'align': 'center',
                    'valign': 'vcenter',
                    'border': 2,
                }
            )

            subtitle_format = workbook.add_format(
                {'bold': True, 'bg_color': '#d9d9d9', 'border': 1}
            )

            count_format = workbook.add_format({'align': 'right', 'border': 1})

            # Add title
            summary_sheet.merge_range('A1:B1', 'Podsumowanie inwentarza', title_format)

            # Add dates section
            row_num = 2
            summary_sheet.write(row_num, 0, 'Data eksportu', subtitle_format)
            summary_sheet.write(
                row_num, 1, timezone.now().strftime('%Y-%m-%d'), count_format
            )

            # Add filter criteria used
            row_num += 2
            summary_sheet.write(row_num, 0, 'Kryteria filtrowania', title_format)
            summary_sheet.write(row_num, 1, '', title_format)

            row_num += 1
            if room_id:
                room_name = Room.objects.get(id=room_id).name
                summary_sheet.write(row_num, 0, 'Pokój', subtitle_format)
                summary_sheet.write(row_num, 1, room_name, count_format)
                row_num += 1

            if rack_id:
                rack_name = Rack.objects.get(id=rack_id).name
                summary_sheet.write(row_num, 0, 'Regał', subtitle_format)
                summary_sheet.write(row_num, 1, rack_name, count_format)
                row_num += 1

            if shelf_id:
                shelf_number = Shelf.objects.get(id=shelf_id).number
                summary_sheet.write(row_num, 0, 'Półka', subtitle_format)
                summary_sheet.write(row_num, 1, str(shelf_number), count_format)
                row_num += 1

            if category_id:
                category_name = Category.objects.get(id=category_id).name
                summary_sheet.write(row_num, 0, 'Kategoria', subtitle_format)
                summary_sheet.write(row_num, 1, category_name, count_format)
                row_num += 1

            summary_sheet.write(row_num, 0, 'Uwzględnij przedmioty przeterminowane', subtitle_format)
            summary_sheet.write(
                row_num, 1, 'Tak' if include_expired else 'Nie', count_format
            )
            row_num += 1

            summary_sheet.write(row_num, 0, 'Uwzględnij przedmioty usunięte', subtitle_format)
            summary_sheet.write(
                row_num, 1, 'Tak' if include_removed else 'Nie', count_format
            )

            # Add statistics
            row_num += 2
            summary_sheet.write(row_num, 0, 'Statystyki', title_format)
            summary_sheet.write(row_num, 1, '', title_format)

            row_num += 1
            summary_sheet.write(row_num, 0, 'Łączna liczba przedmiotów', subtitle_format)
            summary_sheet.write(row_num, 1, assignments.count(), count_format)
            row_num += 1

            # Count active items (not removed)
            active_count = sum(1 for a in assignments if not a.remove_date)
            summary_sheet.write(row_num, 0, 'Aktywne przedmioty', subtitle_format)
            summary_sheet.write(row_num, 1, active_count, count_format)
            row_num += 1

            # Count removed items
            removed_count = sum(1 for a in assignments if a.remove_date)
            summary_sheet.write(row_num, 0, 'Usunięte przedmioty', subtitle_format)
            summary_sheet.write(row_num, 1, removed_count, count_format)
            row_num += 1

            # Count expired items
            expired_count = sum(
                1
                for a in assignments
                if a.item.expiration_date and a.item.expiration_date < today
            )
            summary_sheet.write(row_num, 0, 'Przeterminowane przedmioty', subtitle_format)
            summary_sheet.write(row_num, 1, expired_count, count_format)
            row_num += 1

            # Count items expiring in next 30 days
            expiring_soon = sum(
                1
                for a in assignments
                if a.item.expiration_date
                and today <= a.item.expiration_date <= today + timedelta(days=30)
            )
            summary_sheet.write(row_num, 0, 'Przedmioty kończące się w ciągu 30 dni', subtitle_format)
            summary_sheet.write(row_num, 1, expiring_soon, count_format)
            row_num += 1

            # Add breakdown by category
            row_num += 2
            summary_sheet.write(row_num, 0, 'Przedmioty według kategorii', title_format)
            summary_sheet.write(row_num, 1, '', title_format)
            row_num += 1

            # Get category statistics
            category_stats = {}
            for assignment in assignments:
                category_name = assignment.item.category.name
                if category_name not in category_stats:
                    category_stats[category_name] = 0
                category_stats[category_name] += 1

            # Sort categories by name and write to sheet
            for category_name in sorted(category_stats.keys()):
                summary_sheet.write(row_num, 0, category_name, subtitle_format)
                summary_sheet.write(
                    row_num, 1, category_stats[category_name], count_format
                )
                row_num += 1

            # Add breakdown by location
            row_num += 2
            summary_sheet.write(row_num, 0, 'Przedmioty według lokalizacji', title_format)
            summary_sheet.write(row_num, 1, '', title_format)
            row_num += 1

            # Get location statistics
            location_stats = {}
            for assignment in assignments:
                location = assignment.shelf.full_location
                if location not in location_stats:
                    location_stats[location] = 0
                location_stats[location] += 1

            # Sort locations and write to sheet
            for location in sorted(location_stats.keys()):
                summary_sheet.write(row_num, 0, location, subtitle_format)
                summary_sheet.write(row_num, 1, location_stats[location], count_format)
                row_num += 1

            # Close the workbook
            workbook.close()

            # Create the HTTP response
            output.seek(0)
            response = HttpResponse(
                output.read(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )

            # Define filename based on export parameters
            filename_parts = ['inventory']

            if room_id:
                room_name = Room.objects.get(id=room_id).name
                filename_parts.append(f'room-{room_name}')

            if category_id:
                category_name = Category.objects.get(id=category_id).name
                filename_parts.append(f'cat-{category_name}')

            filename_parts.append(timezone.now().strftime('%Y-%m-%d'))
            filename = '_'.join(filename_parts) + '.xlsx'
            filename = filename.replace(' ', '_').lower()

            response['Content-Disposition'] = f'attachment; filename="{filename}"'

            messages.success(request, 'Inwentarz został pomyślnie wyeksportowany.')
            return response
        else:
            # If form is invalid, add error messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error in {field}: {error}")
    else:
        form = ExportForm()

    # If no POST or form is invalid, show the form
    return render(
        request,
        'warehouse/export_form.html',
        {
            'form': form,
            'rooms': rooms,
            'racks': racks,
            'shelves': shelves,
            'categories': categories,
        },
    )


# AJAX views for dynamic filtering and autocomplete
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
    # Return all racks, but add room_name to help with display
    racks = Rack.objects.all().select_related('room')
    
    if (room_id):
        # Filter by room if specified, but include needed properties
        racks = racks.filter(room_id=room_id)
    
    rack_data = [
        {
            'id': r.id, 
            'name': r.name, 
            'room_id': r.room.id,
            'room_name': r.room.name
        } for r in racks
    ]
    
    return JsonResponse(rack_data, safe=False)


@login_required
def get_shelves(request):
    """AJAX view for getting shelves by rack"""
    rack_id = request.GET.get('rack')
    shelves = Shelf.objects.all().select_related('rack', 'rack__room')
    
    if rack_id:
        # Filter by rack if specified
        shelves = shelves.filter(rack_id=rack_id)
    
    shelf_data = [
        {
            'id': s.id, 
            'number': s.number,
            'rack_id': s.rack.id,
            'room_id': s.rack.room.id,
            'full_location': s.full_location
        } for s in shelves
    ]
    
    return JsonResponse(shelf_data, safe=False)


@login_required
def autocomplete_items(request):
    """AJAX view for item name autocomplete"""
    query = request.GET.get('term', '')

    # Get distinct item names only, not full objects
    if query:
        # Filter by the query but only get distinct names
        items = Item.objects.filter(name__icontains=query).values('name').distinct()
    else:
        # For empty queries, get all distinct names
        items = Item.objects.values('name').distinct()

    # Format results with only name information
    results = []
    # Use .values('name') to ensure we're only getting distinct names
    for item in (
        items[:500] if not query else items[:10]
    ):  # Limit to 500 items for client-side filtering
        item_data = {
            'id': item['name'],
            'text': item['name'],
        }
        results.append(item_data)

    return JsonResponse({'results': results})


@login_required
def autocomplete_manufacturers(request):
    """AJAX view for manufacturer autocomplete"""
    query = request.GET.get('term', '')

    # Base query - exclude null manufacturers
    base_query = Item.objects.filter(manufacturer__isnull=False)

    # If the query is empty, return all distinct manufacturers
    # Otherwise filter based on the query
    if query:
        manufacturers = (
            base_query.filter(manufacturer__icontains=query)
            .values_list('manufacturer', flat=True)
            .distinct()[:10]
        )
    else:
        # For an empty query, get all distinct manufacturers
        manufacturers = base_query.values_list('manufacturer', flat=True).distinct()

    results = [{'id': m, 'text': m} for m in manufacturers]
    return JsonResponse({'results': results})


# User account views
@login_required
def profile(request):
    """User profile view"""
    return render(request, 'warehouse/profile.html')


@login_required
def change_password(request):
    """Change password view"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(
                request, user
            )  # Important to keep the user logged in
            messages.success(request, 'Twoje hasło zostało pomyślnie zmienione!')
            return redirect('warehouse:profile')
        else:
            messages.error(request, 'Proszę poprawić błędy w formularzu.')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'warehouse/change_password.html', {'form': form})


def custom_logout(request):
    """Custom logout view to ensure proper redirection"""
    logout(request)
    messages.success(request, 'Zostałeś pomyślnie wylogowany.')
    return redirect('login')


# Authentication views
def register(request):
    """Registration view for new users"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                'Konto zostało pomyślnie utworzone! Możesz się teraz zalogować.',
            )
            return redirect('login')
    else:
        form = CustomUserCreationForm()

    return render(request, 'registration/register.html', {'form': form})


@login_required
def low_stock(request):
    """View for categories with low stock"""
    categories = Category.objects.annotate(
        active_items=Count(
            'items__assignments', filter=Q(items__assignments__remove_date__isnull=True)
        )
    ).filter(active_items__lt=10)

    low_stock_categories = []
    for category in categories:
        locations = ItemShelfAssignment.objects.filter(
            item__category=category, remove_date__isnull=True
        ).select_related('shelf__rack__room')
        # Deduplicate shelves by their id
        seen_shelf_ids = set()
        location_data = []
        for assignment in locations:
            shelf_id = assignment.shelf.id
            if shelf_id not in seen_shelf_ids:
                seen_shelf_ids.add(shelf_id)
                location_data.append({
                    'id': shelf_id,
                    'full_location': assignment.shelf.full_location,
                    'path': reverse(
                        'warehouse:shelf_detail', kwargs={'pk': shelf_id}
                    ),
                })
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
