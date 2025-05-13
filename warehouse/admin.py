from django.contrib import admin
from .models import Room, Rack, Shelf, Category, Item, ItemShelfAssignment


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Rack)
class RackAdmin(admin.ModelAdmin):
    list_display = ('name', 'room')
    list_filter = ('room',)
    search_fields = ('name', 'room__name')


@admin.register(Shelf)
class ShelfAdmin(admin.ModelAdmin):
    list_display = ('number', 'rack', 'full_location')
    list_filter = ('rack__room', 'rack')
    search_fields = ('number', 'rack__name', 'rack__room__name')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'manufacturer', 'expiration_date', 'is_gifted')
    list_filter = ('category', 'is_gifted')
    search_fields = ('name', 'manufacturer', 'note')
    date_hierarchy = 'expiration_date'


@admin.register(ItemShelfAssignment)
class ItemShelfAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        'item',
        'shelf',
        'added_by',
        'add_date',
        'removed_by',
        'remove_date',
        'is_active_status',
    )
    list_filter = ('shelf__rack__room', 'item__category')
    search_fields = ('item__name', 'shelf__rack__room__name')
    date_hierarchy = 'add_date'
    readonly_fields = ('add_date',)

    def is_active_status(self, obj):
        return obj.remove_date is None

    is_active_status.boolean = True
    is_active_status.short_description = 'Active'
