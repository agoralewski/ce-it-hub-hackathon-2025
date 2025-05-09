import json
import qrcode
import io
import xlsxwriter
from datetime import datetime, timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.core.mail import send_mail
from django.db.models import Count, Q
from django.urls import reverse
from django.utils import timezone
from django.conf import settings

from .models import Room, Rack, Shelf, Category, Item, ItemShelfAssignment
from .forms import (
    RoomForm, RackForm, ShelfForm, CategoryForm, ItemForm, 
    ItemShelfAssignmentForm, ExportForm
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
        shelf_count=Count('racks__shelves')
    )
    
    # Get active item assignments
    active_items = ItemShelfAssignment.objects.filter(
        remove_date__isnull=True
    ).count()
    
    # Get expiring items (within next 30 days)
    expiring_soon = ItemShelfAssignment.objects.filter(
        remove_date__isnull=True,
        item__expiration_date__isnull=False,
        item__expiration_date__lte=datetime.now().date() + timedelta(days=30)
    ).count()
    
    return render(request, 'warehouse/index.html', {
        'rooms': rooms,
        'active_items': active_items,
        'expiring_soon': expiring_soon,
    })


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
    
    if room_id:
        assignments = assignments.filter(shelf__rack__room_id=room_id)
    if rack_id:
        assignments = assignments.filter(shelf__rack_id=rack_id)
    if shelf_id:
        assignments = assignments.filter(shelf_id=shelf_id)
    if category_id:
        assignments = assignments.filter(item__category_id=category_id)
    
    # Get filter options
    rooms = Room.objects.all()
    racks = Rack.objects.all()
    if room_id:
        racks = racks.filter(room_id=room_id)
    
    shelves = Shelf.objects.all()
    if rack_id:
        shelves = shelves.filter(rack_id=rack_id)
    
    categories = Category.objects.all()
    
    return render(request, 'warehouse/item_list.html', {
        'assignments': assignments,
        'rooms': rooms,
        'racks': racks,
        'shelves': shelves,
        'categories': categories,
        'selected_room': room_id,
        'selected_rack': rack_id,
        'selected_shelf': shelf_id,
        'selected_category': category_id,
    })


# Room, rack, and shelf management (admin views)
@login_required
@user_passes_test(is_admin)
def room_list(request):
    """List of all rooms with their racks and shelves"""
    rooms = Room.objects.all().prefetch_related('racks', 'racks__shelves')
    return render(request, 'warehouse/room_list.html', {'rooms': rooms})


@login_required
@user_passes_test(is_admin)
def room_create(request):
    """Create a new room"""
    if request.method == 'POST':
        form = RoomForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Room created successfully.')
            return redirect('warehouse:room_list')
    else:
        form = RoomForm()
    
    return render(request, 'warehouse/room_form.html', {
        'form': form,
        'title': 'Create Room'
    })


@login_required
@user_passes_test(is_admin)
def room_update(request, pk):
    """Update an existing room"""
    room = get_object_or_404(Room, pk=pk)
    
    if request.method == 'POST':
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            messages.success(request, 'Room updated successfully.')
            return redirect('warehouse:room_list')
    else:
        form = RoomForm(instance=room)
    
    return render(request, 'warehouse/room_form.html', {
        'form': form,
        'title': 'Update Room'
    })


@login_required
@user_passes_test(is_admin)
def room_delete(request, pk):
    """Delete a room"""
    room = get_object_or_404(Room, pk=pk)
    
    # Check if room has any items
    has_items = ItemShelfAssignment.objects.filter(
        shelf__rack__room=room,
        remove_date__isnull=True
    ).exists()
    
    if request.method == 'POST':
        if 'confirm' in request.POST:
            room.delete()
            messages.success(request, 'Room deleted successfully.')
            return redirect('warehouse:room_list')
    
    return render(request, 'warehouse/room_delete.html', {
        'room': room,
        'has_items': has_items
    })


@login_required
@user_passes_test(is_admin)
def rack_create(request, room_id):
    """Create a new rack in a room"""
    room = get_object_or_404(Room, pk=room_id)
    
    if request.method == 'POST':
        form = RackForm(request.POST)
        if form.is_valid():
            rack = form.save(commit=False)
            rack.room = room
            rack.save()
            messages.success(request, 'Rack created successfully.')
            return redirect('warehouse:room_list')
    else:
        form = RackForm()
    
    return render(request, 'warehouse/rack_form.html', {
        'form': form,
        'room': room,
        'title': 'Create Rack'
    })


@login_required
@user_passes_test(is_admin)
def rack_update(request, pk):
    """Update an existing rack"""
    rack = get_object_or_404(Rack, pk=pk)
    
    if request.method == 'POST':
        form = RackForm(request.POST, instance=rack)
        if form.is_valid():
            form.save()
            messages.success(request, 'Rack updated successfully.')
            return redirect('warehouse:room_list')
    else:
        form = RackForm(instance=rack)
    
    return render(request, 'warehouse/rack_form.html', {
        'form': form,
        'room': rack.room,
        'title': 'Update Rack'
    })


@login_required
@user_passes_test(is_admin)
def rack_delete(request, pk):
    """Delete a rack"""
    rack = get_object_or_404(Rack, pk=pk)
    
    # Check if rack has any items
    has_items = ItemShelfAssignment.objects.filter(
        shelf__rack=rack,
        remove_date__isnull=True
    ).exists()
    
    if request.method == 'POST':
        if 'confirm' in request.POST:
            rack.delete()
            messages.success(request, 'Rack deleted successfully.')
            return redirect('warehouse:room_list')
    
    return render(request, 'warehouse/rack_delete.html', {
        'rack': rack,
        'has_items': has_items
    })


@login_required
@user_passes_test(is_admin)
def shelf_create(request, rack_id):
    """Create a new shelf in a rack"""
    rack = get_object_or_404(Rack, pk=rack_id)
    
    if request.method == 'POST':
        form = ShelfForm(request.POST)
        if form.is_valid():
            shelf = form.save(commit=False)
            shelf.rack = rack
            shelf.save()
            messages.success(request, 'Shelf created successfully.')
            return redirect('warehouse:room_list')
    else:
        form = ShelfForm()
    
    return render(request, 'warehouse/shelf_form.html', {
        'form': form,
        'rack': rack,
        'title': 'Create Shelf'
    })


@login_required
@user_passes_test(is_admin)
def shelf_update(request, pk):
    """Update an existing shelf"""
    shelf = get_object_or_404(Shelf, pk=pk)
    
    if request.method == 'POST':
        form = ShelfForm(request.POST, instance=shelf)
        if form.is_valid():
            form.save()
            messages.success(request, 'Shelf updated successfully.')
            return redirect('warehouse:room_list')
    else:
        form = ShelfForm(instance=shelf)
    
    return render(request, 'warehouse/shelf_form.html', {
        'form': form,
        'rack': shelf.rack,
        'title': 'Update Shelf'
    })


@login_required
@user_passes_test(is_admin)
def shelf_delete(request, pk):
    """Delete a shelf"""
    shelf = get_object_or_404(Shelf, pk=pk)
    
    # Check if shelf has any items
    has_items = ItemShelfAssignment.objects.filter(
        shelf=shelf,
        remove_date__isnull=True
    ).exists()
    
    if request.method == 'POST':
        if 'confirm' in request.POST:
            shelf.delete()
            messages.success(request, 'Shelf deleted successfully.')
            return redirect('warehouse:room_list')
    
    return render(request, 'warehouse/shelf_delete.html', {
        'shelf': shelf,
        'has_items': has_items
    })


# Category management
@login_required
@user_passes_test(is_admin)
def category_list(request):
    """List of all categories"""
    categories = Category.objects.all()
    return render(request, 'warehouse/category_list.html', {'categories': categories})


@login_required
@user_passes_test(is_admin)
def category_create(request):
    """Create a new category"""
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category created successfully.')
            return redirect('warehouse:category_list')
    else:
        form = CategoryForm()
    
    return render(request, 'warehouse/category_form.html', {
        'form': form,
        'title': 'Create Category'
    })


@login_required
@user_passes_test(is_admin)
def category_update(request, pk):
    """Update an existing category"""
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated successfully.')
            return redirect('warehouse:category_list')
    else:
        form = CategoryForm(instance=category)
    
    return render(request, 'warehouse/category_form.html', {
        'form': form,
        'title': 'Update Category'
    })


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
            messages.success(request, 'Category deleted successfully.')
            return redirect('warehouse:category_list')
    
    return render(request, 'warehouse/category_delete.html', {
        'category': category,
        'has_items': has_items
    })


# Shelf detail view and item management
@login_required
def shelf_detail(request, pk):
    """Detail view of a shelf with its items"""
    shelf = get_object_or_404(Shelf, pk=pk)
    
    # Get active assignments
    assignments = ItemShelfAssignment.objects.filter(
        shelf=shelf,
        remove_date__isnull=True
    ).select_related('item', 'added_by')
    
    return render(request, 'warehouse/shelf_detail.html', {
        'shelf': shelf,
        'assignments': assignments
    })


@login_required
def add_item_to_shelf(request, shelf_id):
    """Add an item to a shelf"""
    shelf = get_object_or_404(Shelf, pk=shelf_id)
    
    if request.method == 'POST':
        form = ItemShelfAssignmentForm(request.POST)
        
        if form.is_valid():
            # Create or get the item
            item_data = {
                'name': form.cleaned_data['item_name'],
                'category': form.cleaned_data['category'],
                'manufacturer': form.cleaned_data['manufacturer'],
                'expiration_date': form.cleaned_data['expiration_date'],
                'note': form.cleaned_data['notes'],
            }
            
            item = Item.objects.create(**item_data)
            
            # Create assignment
            ItemShelfAssignment.objects.create(
                item=item,
                shelf=shelf,
                added_by=request.user
            )
            
            messages.success(request, 'Item added to shelf successfully.')
            return redirect('warehouse:shelf_detail', pk=shelf_id)
    else:
        form = ItemShelfAssignmentForm()
    
    return render(request, 'warehouse/add_item.html', {
        'form': form,
        'shelf': shelf
    })


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
        
        messages.success(request, 'Item removed from shelf successfully.')
        return redirect('warehouse:shelf_detail', pk=assignment.shelf.pk)
    
    return render(request, 'warehouse/remove_item.html', {
        'assignment': assignment
    })


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
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="shelf_qr_codes.pdf"'
            
            # Create PDF with QR codes
            # This is a placeholder. In a real implementation, you would use
            # a PDF library like ReportLab to generate the PDF with QR codes
            
            messages.success(request, 'QR codes generated successfully.')
            return response
    
    return render(request, 'warehouse/generate_qr_codes.html', {
        'shelves': shelves
    })


# Excel export
@login_required
@user_passes_test(is_admin)
def export_inventory(request):
    """Export inventory to Excel"""
    rooms = Room.objects.all()
    racks = Rack.objects.all()
    shelves = Shelf.objects.all()
    
    if request.method == 'POST':
        form = ExportForm(request.POST)
        
        if form.is_valid():
            room_id = form.cleaned_data.get('room')
            rack_id = form.cleaned_data.get('rack')
            shelf_id = form.cleaned_data.get('shelf')
            
            # Build query based on form data
            query = Q(remove_date__isnull=True)
            
            if shelf_id:
                query &= Q(shelf_id=shelf_id)
            elif rack_id:
                query &= Q(shelf__rack_id=rack_id)
            elif room_id:
                query &= Q(shelf__rack__room_id=room_id)
            
            assignments = ItemShelfAssignment.objects.filter(query).select_related(
                'item', 'shelf', 'shelf__rack', 'shelf__rack__room'
            )
            
            # Create Excel file
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output)
            worksheet = workbook.add_worksheet('Inventory')
            
            # Add header
            headers = [
                'Item Name', 'Category', 'Manufacturer', 'Expiration Date',
                'Location', 'Added By', 'Add Date', 'Notes'
            ]
            
            for col, header in enumerate(headers):
                worksheet.write(0, col, header)
            
            # Add data
            for row, assignment in enumerate(assignments, start=1):
                item = assignment.item
                worksheet.write(row, 0, item.name)
                worksheet.write(row, 1, item.category.name)
                worksheet.write(row, 2, item.manufacturer or '')
                if item.expiration_date:
                    worksheet.write(row, 3, item.expiration_date.strftime('%Y-%m-%d'))
                else:
                    worksheet.write(row, 3, '')
                worksheet.write(row, 4, assignment.shelf.full_location)
                worksheet.write(row, 5, assignment.added_by.username)
                worksheet.write(row, 6, assignment.add_date.strftime('%Y-%m-%d %H:%M'))
                worksheet.write(row, 7, item.note or '')
            
            workbook.close()
            output.seek(0)
            
            # Create response
            filename = 'inventory_export_{}.xlsx'.format(datetime.now().strftime('%Y%m%d_%H%M%S'))
            response = HttpResponse(
                output,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
            
            return response
    else:
        form = ExportForm()
    
    return render(request, 'warehouse/export_form.html', {
        'form': form,
        'rooms': rooms,
        'racks': racks,
        'shelves': shelves
    })


# AJAX autocomplete views
@login_required
def autocomplete_categories(request):
    """AJAX view for category autocomplete"""
    query = request.GET.get('term', '')
    categories = Category.objects.filter(name__icontains=query)[:10]
    results = [{'id': c.id, 'text': c.name} for c in categories]
    return JsonResponse({'results': results})


@login_required
def autocomplete_items(request):
    """AJAX view for item name autocomplete"""
    query = request.GET.get('term', '')
    items = Item.objects.filter(name__icontains=query).distinct()[:10]
    results = [{'id': i.id, 'text': i.name} for i in items]
    return JsonResponse({'results': results})


@login_required
def autocomplete_manufacturers(request):
    """AJAX view for manufacturer autocomplete"""
    query = request.GET.get('term', '')
    manufacturers = Item.objects.filter(
        manufacturer__isnull=False,
        manufacturer__icontains=query
    ).values_list('manufacturer', flat=True).distinct()[:10]
    results = [{'id': m, 'text': m} for m in manufacturers]
    return JsonResponse({'results': results})


# User profile and password management
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
            update_session_auth_hash(request, user)  # Keep user logged in
            messages.success(request, 'Your password was successfully updated!')
            return redirect('warehouse:profile')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'warehouse/change_password.html', {
        'form': form
    })
