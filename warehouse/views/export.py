"""
Export and QR code generation views.
"""

import io
import xlsxwriter
from datetime import timedelta

from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponse
from django.urls import reverse
from django.utils import timezone
from django.db.models import Q

from warehouse.models import Room, Rack, Shelf, Category, ItemShelfAssignment
from warehouse.forms import ExportForm
from warehouse.views.utils import is_admin


@login_required
@user_passes_test(is_admin)
def generate_qr_codes(request):
    """Generate QR codes for shelves"""
    # Get shelves with related entities to reduce db queries
    shelves = (
        Shelf.objects.all()
        .select_related('rack', 'rack__room')
        .order_by('rack__room__name', 'rack__name', 'number')
    )

    if request.method == 'POST':
        selected_shelves = request.POST.getlist('shelves')

        if selected_shelves:
            # Create an in-memory PDF file with QR codes
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.units import mm
            import qrcode
            import io
            import tempfile
            import os

            # Get the selected shelves - select_related to avoid additional queries
            selected_shelves = (
                Shelf.objects.filter(id__in=selected_shelves)
                .select_related('rack', 'rack__room')
                .order_by('rack__room__name', 'rack__name', 'number')
            )

            # Create a BytesIO buffer to receive the PDF data
            buffer = io.BytesIO()

            # Get the page dimensions
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
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )

                # Make sure each shelf has a UUID
                if not shelf.qr_code_uuid:
                    shelf.save()  # This will trigger the UUID generation

                # Create the URL for the shelf detail page with the network IP
                from warehouse.views.utils import build_network_absolute_uri

                shelf_url = build_network_absolute_uri(
                    request, reverse('warehouse:shelf_detail', kwargs={'pk': shelf.pk})
                )

                qr.add_data(shelf_url)
                qr.make(fit=True)

                # Create an image from the QR Code instance
                img = qr.make_image(fill_color='black', back_color='white')

                # Create a temporary file for the image
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                temp_filename = temp_file.name

                # Save the image to the temporary file
                img.save(temp_filename)

                # Draw the QR code image on the canvas from the file
                p.drawImage(temp_filename, x, y, width=qr_size, height=qr_size)

                # Clean up the temporary file
                try:
                    os.unlink(temp_filename)
                except:  # noqa
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

            # Handle expiration filter - only filter out expired items if include_expired is False
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

            # Base formats
            cell_format = workbook.add_format({'border': 1})
            date_format = workbook.add_format({'border': 1, 'num_format': 'yyyy-mm-dd'})

            # Special condition formats with corresponding date formats
            expired_format = workbook.add_format(
                {'bg_color': '#ff0000', 'border': 1}
            )  # Red
            expired_date_format = workbook.add_format(
                {'bg_color': '#ff0000', 'border': 1, 'num_format': 'yyyy-mm-dd'}
            )

            nearly_expired_format = workbook.add_format(
                {'bg_color': '#FFA500', 'border': 1}
            )  # Orange
            nearly_expired_date_format = workbook.add_format(
                {'bg_color': '#FFA500', 'border': 1, 'num_format': 'yyyy-mm-dd'}
            )

            removed_format = workbook.add_format(
                {'color': '#888888', 'italic': True, 'border': 1}
            )
            removed_date_format = workbook.add_format(
                {
                    'color': '#888888',
                    'italic': True,
                    'border': 1,
                    'num_format': 'yyyy-mm-dd',
                }
            )

            # Create main inventory worksheet
            worksheet = workbook.add_worksheet('Inwentarz')
            worksheet.set_column('A:A', 25)  # Nazwa przedmiotu
            worksheet.set_column('B:B', 15)  # Kategoria
            worksheet.set_column('C:C', 15)  # Producent
            worksheet.set_column('D:D', 25)  # Notatka
            worksheet.set_column('E:E', 12)  # Data ważności
            worksheet.set_column('F:F', 20)  # Lokalizacja
            worksheet.set_column('G:G', 8)  # Liczba
            worksheet.set_column('H:H', 12)  # Data usunięcia

            # Add header with Polish names
            headers = [
                'Nazwa przedmiotu',
                'Kategoria',
                'Producent',
                'Notatka',
                'Data Waznosci',
                'Lokalizacja',
                'Liczba',
                'Data Usuniecia',
            ]

            for col, header in enumerate(headers):
                worksheet.write(0, col, header, header_format)

            # Add data
            today = timezone.now().date()

            # Group assignments by item name, shelf, category, and other properties
            # Similar to item_list view to maintain the same level of aggregation
            from django.db.models import Count, F, Max, Case, When, Value, BooleanField

            # Group items for the export
            grouped_items_query = (
                assignments.values(
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
                    is_removed=Case(
                        When(remove_date__isnull=False, then=Value(True)),
                        default=Value(False),
                        output_field=BooleanField(),
                    ),
                    latest_remove_date=Max('remove_date'),
                )
                .order_by('item__name', 'shelf__id', 'is_removed')
            )

            # Fetch related objects in bulk
            shelf_ids = {item['shelf_id'] for item in grouped_items_query}
            shelves = {
                shelf.id: shelf
                for shelf in Shelf.objects.filter(id__in=shelf_ids).select_related(
                    'rack', 'rack__room'
                )
            }

            category_ids = {item['category_id'] for item in grouped_items_query}
            categories = {
                category.id: category
                for category in Category.objects.filter(id__in=category_ids)
            }

            # Using the nearly_expired_format already defined above

            row = 1  # Start from row 1 (after header)

            for group in grouped_items_query:
                shelf = shelves.get(group['shelf_id'])
                category = categories.get(group['category_id'])

                is_removed = group['is_removed']
                removal_date = group['latest_remove_date'] if is_removed else None

                # Use removed style for any group with a removal date (i.e., removed items)
                if is_removed:
                    current_format = removed_format
                else:
                    # Only use expired/nearly expired style for active items
                    is_expired = (
                        group['expiration_date'] and group['expiration_date'] < today
                    )
                    is_nearly_expired = group['expiration_date'] and today <= group[
                        'expiration_date'
                    ] <= today + timedelta(days=30)
                    if is_expired:
                        current_format = expired_format
                    elif is_nearly_expired:
                        current_format = nearly_expired_format
                    else:
                        current_format = cell_format

                # Write the row data with appropriate formatting
                worksheet.write(row, 0, group['item_name'], current_format)  # Name
                worksheet.write(row, 1, category.name, current_format)  # Category
                worksheet.write(
                    row, 2, group['manufacturer'] or '', current_format
                )  # Manufacturer
                worksheet.write(row, 3, group['note'] or '', current_format)  # Note

                # Expiration date - for removed items, always use removed_format, not expiration logic
                if group['expiration_date']:
                    if is_removed:
                        worksheet.write_datetime(
                            row, 4, group['expiration_date'], removed_date_format
                        )
                    elif is_expired:
                        worksheet.write_datetime(
                            row, 4, group['expiration_date'], expired_date_format
                        )
                    elif is_nearly_expired:
                        worksheet.write_datetime(
                            row, 4, group['expiration_date'], nearly_expired_date_format
                        )
                    else:
                        worksheet.write_datetime(
                            row, 4, group['expiration_date'], date_format
                        )
                else:
                    worksheet.write(row, 4, '', current_format)

                # Location
                worksheet.write(row, 5, shelf.full_location, current_format)

                # Count (quantity)
                worksheet.write(row, 6, group['count'], current_format)

                # Removal date (only for removed items)
                if is_removed and removal_date:
                    worksheet.write_datetime(row, 7, removal_date, removed_date_format)
                else:
                    worksheet.write(row, 7, '', current_format)

                row += 1

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

            summary_sheet.write(
                row_num, 0, 'Uwzględnij przedmioty przeterminowane', subtitle_format
            )
            summary_sheet.write(
                row_num, 1, 'Tak' if include_expired else 'Nie', count_format
            )
            row_num += 1

            summary_sheet.write(
                row_num, 0, 'Uwzględnij przedmioty usunięte', subtitle_format
            )
            summary_sheet.write(
                row_num, 1, 'Tak' if include_removed else 'Nie', count_format
            )

            # Add statistics
            row_num += 2
            summary_sheet.write(row_num, 0, 'Statystyki', title_format)
            summary_sheet.write(row_num, 1, '', title_format)

            row_num += 1
            summary_sheet.write(
                row_num, 0, 'Łączna liczba przedmiotów', subtitle_format
            )
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
            summary_sheet.write(
                row_num, 0, 'Przeterminowane przedmioty', subtitle_format
            )
            summary_sheet.write(row_num, 1, expired_count, count_format)
            row_num += 1

            # Count items expiring in next 30 days
            expiring_soon = sum(
                1
                for a in assignments
                if a.item.expiration_date
                and today <= a.item.expiration_date <= today + timedelta(days=30)
            )
            summary_sheet.write(
                row_num, 0, 'Przedmioty kończące się w ciągu 30 dni', subtitle_format
            )
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
            summary_sheet.write(
                row_num, 0, 'Przedmioty według lokalizacji', title_format
            )
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
                    messages.error(request, f'Error in {field}: {error}')
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
