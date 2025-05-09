from django.urls import path
from . import views

app_name = 'warehouse'

urlpatterns = [
    # Main views
    path('', views.index, name='index'),
    path('items/', views.item_list, name='item_list'),
    
    # Room, rack, and shelf management (admin)
    path('rooms/', views.room_list, name='room_list'),
    path('rooms/create/', views.room_create, name='room_create'),
    path('rooms/<int:pk>/update/', views.room_update, name='room_update'),
    path('rooms/<int:pk>/delete/', views.room_delete, name='room_delete'),
    path('rooms/<int:room_id>/racks/create/', views.rack_create, name='rack_create'),
    path('racks/<int:pk>/update/', views.rack_update, name='rack_update'),
    path('racks/<int:pk>/delete/', views.rack_delete, name='rack_delete'),
    path('racks/<int:rack_id>/shelves/create/', views.shelf_create, name='shelf_create'),
    path('shelves/<int:pk>/update/', views.shelf_update, name='shelf_update'),
    path('shelves/<int:pk>/delete/', views.shelf_delete, name='shelf_delete'),
    
    # Category management (admin)
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:pk>/update/', views.category_update, name='category_update'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
    
    # Shelf detail view and item management
    path('shelves/<int:pk>/', views.shelf_detail, name='shelf_detail'),
    path('shelves/<int:shelf_id>/add_item/', views.add_item_to_shelf, name='add_item_to_shelf'),
    path('assignments/<int:pk>/remove/', views.remove_item_from_shelf, name='remove_item_from_shelf'),
    
    # QR code generation
    path('qrcodes/', views.generate_qr_codes, name='generate_qr_codes'),
    
    # Excel export
    path('export/', views.export_inventory, name='export_inventory'),
    
    # AJAX endpoints for autocomplete
    path('api/autocomplete/categories/', views.autocomplete_categories, name='autocomplete_categories'),
    path('api/autocomplete/items/', views.autocomplete_items, name='autocomplete_items'),
    path('api/autocomplete/manufacturers/', views.autocomplete_manufacturers, name='autocomplete_manufacturers'),
    
    # User profile and password management
    path('profile/', views.profile, name='profile'),
    path('profile/change-password/', views.change_password, name='change_password'),
]
