from django.db import models
from django.contrib.auth.models import User
import uuid


class Room(models.Model):
    name = models.CharField(max_length=100, unique=True)
    qr_code_uuid = models.UUIDField(null=True, blank=True, unique=True)

    def save(self, *args, **kwargs):
        if not self.qr_code_uuid:
            self.qr_code_uuid = uuid.uuid4()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Rack(models.Model):
    name = models.CharField(max_length=1)  # A, B, C, etc.
    room = models.ForeignKey(
        Room, on_delete=models.CASCADE, related_name='racks', db_index=True
    )
    qr_code_uuid = models.UUIDField(null=True, blank=True, unique=True)

    class Meta:
        unique_together = ['name', 'room']
        indexes = [
            models.Index(fields=['room']),
        ]

    def save(self, *args, **kwargs):
        if not self.qr_code_uuid:
            self.qr_code_uuid = uuid.uuid4()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.room.name}.{self.name}'


class Shelf(models.Model):
    number = models.PositiveIntegerField()
    rack = models.ForeignKey(
        Rack, on_delete=models.CASCADE, related_name='shelves', db_index=True
    )
    qr_code_uuid = models.UUIDField(null=True, blank=True, unique=True)

    class Meta:
        unique_together = ['number', 'rack']
        indexes = [
            models.Index(fields=['rack']),
        ]

    def save(self, *args, **kwargs):
        if not self.qr_code_uuid:
            self.qr_code_uuid = uuid.uuid4()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.rack}.{self.number}'

    @property
    def full_location(self):
        return f'{self.rack.room.name}.{self.rack.name}.{self.number}'


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


class Item(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name='items', db_index=True
    )
    manufacturer = models.CharField(
        max_length=255, blank=True, null=True, db_index=True
    )
    expiration_date = models.DateField(blank=True, null=True, db_index=True)
    note = models.TextField(blank=True, null=True)
    is_gifted = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['category']),
            models.Index(fields=['manufacturer']),
            models.Index(fields=['expiration_date']),
        ]

    def __str__(self):
        return self.name


class ItemShelfAssignment(models.Model):
    item = models.ForeignKey(
        Item, on_delete=models.CASCADE, related_name='assignments', db_index=True
    )
    shelf = models.ForeignKey(
        Shelf, on_delete=models.CASCADE, related_name='assignments', db_index=True
    )
    added_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='added_items'
    )
    removed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='removed_items',
    )
    add_date = models.DateTimeField(auto_now_add=True, db_index=True)
    remove_date = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['item']),
            models.Index(fields=['shelf']),
            models.Index(fields=['add_date']),
            models.Index(fields=['remove_date']),
            # Compound index for common filtering operations
            models.Index(fields=['shelf', 'remove_date']),
            models.Index(fields=['item', 'remove_date']),
        ]

    def __str__(self):
        status = 'Active' if not self.remove_date else 'Removed'
        return f'{self.item.name} on {self.shelf} - {status}'

    @property
    def is_active(self):
        return self.remove_date is None
