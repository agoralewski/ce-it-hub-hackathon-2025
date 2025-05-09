from django.db import models
from django.contrib.auth.models import User


class Room(models.Model):
    name = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.name


class Rack(models.Model):
    name = models.CharField(max_length=1)  # A, B, C, etc.
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='racks')
    
    class Meta:
        unique_together = ['name', 'room']
        
    def __str__(self):
        return f"{self.room.name}.{self.name}"


class Shelf(models.Model):
    number = models.PositiveIntegerField()
    rack = models.ForeignKey(Rack, on_delete=models.CASCADE, related_name='shelves')
    
    class Meta:
        unique_together = ['number', 'rack']
        
    def __str__(self):
        return f"{self.rack}.{self.number}"
    
    @property
    def full_location(self):
        return f"{self.rack.room.name}.{self.rack.name}.{self.number}"


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        
    def __str__(self):
        return self.name


class Item(models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='items')
    manufacturer = models.CharField(max_length=255, blank=True, null=True)
    expiration_date = models.DateField(blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    is_gifted = models.BooleanField(default=False)
    
    def __str__(self):
        return self.name


class ItemShelfAssignment(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='assignments')
    shelf = models.ForeignKey(Shelf, on_delete=models.CASCADE, related_name='assignments')
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='added_items')
    removed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='removed_items')
    add_date = models.DateTimeField(auto_now_add=True)
    remove_date = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        status = "Active" if not self.remove_date else "Removed"
        return f"{self.item.name} on {self.shelf} - {status}"
    
    @property
    def is_active(self):
        return self.remove_date is None
