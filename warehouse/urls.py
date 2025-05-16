from django.urls import path
# Import views from their specific modules
from warehouse.views.core import index, item_list, low_stock
from warehouse.views.location import (
    room_list, room_create, room_update, room_delete,
    rack_create, rack_update, rack_delete,
    shelf_create, shelf_update, shelf_delete, shelf_detail
)
from warehouse.views.category import (
    category_list, category_create, category_update, category_delete
)
from warehouse.views.item import (
    add_item_to_shelf, remove_item_from_shelf, ajax_bulk_add_items, ajax_bulk_remove_items,
    add_new_item
)
from warehouse.views.export import (
    generate_qr_codes, export_inventory
)
from warehouse.views.ajax import (
    autocomplete_categories, get_racks, get_shelves,
    autocomplete_items, autocomplete_manufacturers, autocomplete_users
)
from warehouse.views.account import (
    profile, change_password, custom_logout
)
from warehouse.views.history import history_list

app_name = 'warehouse'

urlpatterns = [
    # Main views
    path('', index, name='index'),
    path('items/', item_list, name='item_list'),
    path('history/', history_list, name='history_list'),
    # Room, rack, and shelf management (admin)
    path('rooms/', room_list, name='room_list'),
    path('rooms/create/', room_create, name='room_create'),
    path('rooms/<int:pk>/update/', room_update, name='room_update'),
    path('rooms/<int:pk>/delete/', room_delete, name='room_delete'),
    path('rooms/<int:room_id>/racks/create/', rack_create, name='rack_create'),
    path('racks/<int:pk>/update/', rack_update, name='rack_update'),
    path('racks/<int:pk>/delete/', rack_delete, name='rack_delete'),
    path(
        'racks/<int:rack_id>/shelves/create/', shelf_create, name='shelf_create'
    ),
    path('shelves/<int:pk>/update/', shelf_update, name='shelf_update'),
    path('shelves/<int:pk>/delete/', shelf_delete, name='shelf_delete'),
    # Category management (admin)
    path('categories/', category_list, name='category_list'),
    path('categories/create/', category_create, name='category_create'),
    path('categories/<int:pk>/update/', category_update, name='category_update'),
    path('categories/<int:pk>/delete/', category_delete, name='category_delete'),
    # Shelf detail view and item management
    path('shelves/<int:pk>/', shelf_detail, name='shelf_detail'),
    path(
        'shelves/<int:shelf_id>/add_item/',
        add_item_to_shelf,
        name='add_item_to_shelf',
    ),
    path(
        'items/add/',
        add_new_item,
        name='add_new_item',
    ),
    path(
        'assignments/<int:pk>/remove/',
        remove_item_from_shelf,
        name='remove_item_from_shelf',
    ),
    # QR code generation
    path('qrcodes/', generate_qr_codes, name='generate_qr_codes'),
    # Excel export
    path('export/', export_inventory, name='export_inventory'),
    # AJAX endpoints for autocomplete
    path(
        'api/autocomplete/categories/',
        autocomplete_categories,
        name='autocomplete_categories',
    ),
    path(
        'api/autocomplete/items/', autocomplete_items, name='autocomplete_items'
    ),
    path(
        'api/autocomplete/manufacturers/',
        autocomplete_manufacturers,
        name='autocomplete_manufacturers',
    ),
    path(
        'api/autocomplete/users/',
        autocomplete_users,
        name='autocomplete_users',
    ),
    # AJAX endpoints for dynamic filtering
    path('api/racks/', get_racks, name='get_racks'),
    path('api/shelves/', get_shelves, name='get_shelves'),
    path('ajax/bulk-add-items/', ajax_bulk_add_items, name='ajax_bulk_add_items'),
    path('ajax/bulk-remove-items/', ajax_bulk_remove_items, name='ajax_bulk_remove_items'),
    # User profile and password management
    path('profile/', profile, name='profile'),
    path('profile/change-password/', change_password, name='change_password'),
    path('logout/', custom_logout, name='custom_logout'),
    # Low stock view
    path('low_stock/', low_stock, name='low_stock'),
]
