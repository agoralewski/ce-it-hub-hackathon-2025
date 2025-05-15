"""
Re-exports all views from the views package to maintain backward compatibility.
This module is kept for compatibility with existing imports, but the actual view 
implementations have been moved to the warehouse/views/ package.
"""

# Re-export all views from the views package
from warehouse.views import (
    # Utility functions
    is_admin,
    
    # Core views
    index, item_list, low_stock,
    
    # Location management
    room_list, room_create, room_update, room_delete,
    rack_create, rack_update, rack_delete,
    shelf_create, shelf_update, shelf_delete, shelf_detail,
    
    # Category management
    category_list, category_create, category_update, category_delete,
    
    # Item management
    add_item_to_shelf, remove_item_from_shelf, ajax_bulk_add_items,
    
    # Export and QR codes
    generate_qr_codes, export_inventory,
    
    # AJAX endpoints
    autocomplete_categories, get_racks, get_shelves,
    autocomplete_items, autocomplete_manufacturers,
    
    # Account management
    profile, change_password, custom_logout, register,
)
