"""
Import all views from the views package and re-export them to maintain backward
compatibility with code that imports from the original views.py module.
"""

# Import utility functions
from warehouse.views.utils import is_admin

# Import core views
from warehouse.views.core import index, item_list, low_stock

# Import location management views
from warehouse.views.location import (
    room_list, room_create, room_update, room_delete,
    rack_create, rack_update, rack_delete,
    shelf_create, shelf_update, shelf_delete, shelf_detail
)

# Import category management views
from warehouse.views.category import (
    category_list, category_create, category_update, category_delete
)

# Import item management views
from warehouse.views.item import (
    add_item_to_shelf, remove_item_from_shelf, ajax_bulk_add_items, ajax_bulk_remove_items
)

# Import export and QR code views
from warehouse.views.export import (
    generate_qr_codes, export_inventory
)

# Import AJAX views
from warehouse.views.ajax import (
    autocomplete_categories, get_racks, get_shelves,
    autocomplete_items, autocomplete_manufacturers
)

# Import account views
from warehouse.views.account import (
    profile, edit_profile, change_password, custom_logout, register
)

# Define __all__ to explicitly specify what's exported from this package
__all__ = [
    # Utility functions
    'is_admin',
    
    # Core views
    'index', 'item_list', 'low_stock',
    
    # Location management
    'room_list', 'room_create', 'room_update', 'room_delete',
    'rack_create', 'rack_update', 'rack_delete',
    'shelf_create', 'shelf_update', 'shelf_delete', 'shelf_detail',
    
    # Category management
    'category_list', 'category_create', 'category_update', 'category_delete',
    
    # Item management
    'add_item_to_shelf', 'remove_item_from_shelf', 'ajax_bulk_add_items', 'ajax_bulk_remove_items',
    
    # Export and QR codes
    'generate_qr_codes', 'export_inventory',
    
    # AJAX endpoints
    'autocomplete_categories', 'get_racks', 'get_shelves',
    'autocomplete_items', 'autocomplete_manufacturers',
    
    # Account management
    'profile', 'edit_profile', 'change_password', 'custom_logout', 'register',
]