from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Room, Rack, Shelf, Category, Item, ItemShelfAssignment


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'})
        }


class RackForm(forms.ModelForm):
    class Meta:
        model = Rack
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'})
        }


class ShelfForm(forms.ModelForm):
    class Meta:
        model = Shelf
        fields = ['number']
        widgets = {
            'number': forms.NumberInput(attrs={'class': 'form-control'})
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'})
        }


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['name', 'category', 'manufacturer', 'expiration_date', 'note']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control select2'}),
            'manufacturer': forms.TextInput(attrs={'class': 'form-control'}),
            'expiration_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class ItemShelfAssignmentForm(forms.Form):
    """Form for adding items to shelf"""
    item_name = forms.CharField(
        label="Nazwa przedmiotu",
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control item-autocomplete'})
    )
    category = forms.ModelChoiceField(
        label="Kategoria",
        queryset=Category.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control category-select'})
    )
    quantity = forms.IntegerField(
        label="Ilość",
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    manufacturer = forms.CharField(
        label="Producent",
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control manufacturer-autocomplete'})
    )
    expiration_date = forms.DateField(
        label="Data ważności",
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    notes = forms.CharField(
        label="Notatki",
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )


class ExportForm(forms.Form):
    """Form for exporting inventory"""
    room = forms.ModelChoiceField(
        label="Pokój",
        queryset=Room.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    rack = forms.ModelChoiceField(
        label="Regał",
        queryset=Rack.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    shelf = forms.ModelChoiceField(
        label="Półka",
        queryset=Shelf.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter racks based on selected room
        if 'data' in kwargs and 'room' in kwargs['data'] and kwargs['data']['room']:
            room_id = kwargs['data']['room']
            self.fields['rack'].queryset = Rack.objects.filter(room_id=room_id)
        else:
            self.fields['rack'].queryset = Rack.objects.none()
        
        # Filter shelves based on selected rack
        if 'data' in kwargs and 'rack' in kwargs['data'] and kwargs['data']['rack']:
            rack_id = kwargs['data']['rack']
            self.fields['shelf'].queryset = Shelf.objects.filter(rack_id=rack_id)
        else:
            self.fields['shelf'].queryset = Shelf.objects.none()
