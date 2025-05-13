from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Room, Rack, Shelf, Category, Item


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['name']
        widgets = {'name': forms.TextInput(attrs={'class': 'form-control'})}
        error_messages = {
            'name': {
                'unique': 'Pokój o tej nazwie już istnieje. Proszę wybrać inną nazwę.'
            }
        }

    def clean_name(self):
        name = self.cleaned_data.get('name', '')
        return name.capitalize()


class RackForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.room = kwargs.pop('room', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = Rack
        fields = ['name']
        widgets = {'name': forms.TextInput(attrs={'class': 'form-control'})}
        error_messages = {
            'name': {
                'unique': 'Regał o tej nazwie już istnieje. Proszę wybrać inną nazwę.'
            }
        }

    def clean_name(self):
        name = self.cleaned_data.get('name').capitalize()
        if self.room and Rack.objects.filter(name=name, room=self.room).exists():
            raise forms.ValidationError('Regał o tej nazwie już istnieje w tym pokoju.')
        return name


class ShelfForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.rack = kwargs.pop('rack', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = Shelf
        fields = ['number']
        widgets = {'number': forms.NumberInput(attrs={'class': 'form-control'})}
        error_messages = {
            'number': {
                'unique': 'Półka o tym numerze już istnieje w tym regale. Proszę wybrać inny numer.'
            }
        }

    def clean_number(self):
        number = self.cleaned_data.get('number')
        if self.rack and Shelf.objects.filter(number=number, rack=self.rack).exists():
            raise forms.ValidationError(
                'Półka o tym numerze już istnieje w tym regale.'
            )
        return number


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']
        widgets = {'name': forms.TextInput(attrs={'class': 'form-control'})}
        error_messages = {
            'name': {
                'unique': 'Kategoria o tej nazwie już istnieje. Proszę wybrać inną nazwę.'
            }
        }

    def clean_name(self):
        name = self.cleaned_data.get('name', '')
        return name.capitalize()


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['name', 'category', 'manufacturer', 'expiration_date', 'note']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control select2'}),
            'manufacturer': forms.TextInput(attrs={'class': 'form-control'}),
            'expiration_date': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'}
            ),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_name(self):
        name = self.cleaned_data.get('name', '')
        return name.capitalize()


class ItemShelfAssignmentForm(forms.Form):
    """Form for adding items to shelf"""

    item_name = forms.CharField(
        label='Nazwa przedmiotu',
        max_length=255,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control item-autocomplete',
                'placeholder': 'Wpisz nazwę przedmiotu',
                'autocomplete': 'off',
            }
        ),
    )
    category = forms.ModelChoiceField(
        label='Kategoria',
        queryset=Category.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control category-select'}),
    )
    quantity = forms.IntegerField(
        label='Ilość',
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )
    manufacturer = forms.CharField(
        label='Producent',
        max_length=255,
        required=False,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control manufacturer-autocomplete',
                'placeholder': 'Wpisz producenta',
                'autocomplete': 'off',
            }
        ),
    )
    expiration_date = forms.DateField(
        label='Data ważności',
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )
    notes = forms.CharField(
        label='Notatki',
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
    )


class ExportForm(forms.Form):
    """Form for exporting inventory"""

    room = forms.ModelChoiceField(
        label='Pokój',
        queryset=Room.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    rack = forms.ModelChoiceField(
        label='Regał',
        queryset=Rack.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    shelf = forms.ModelChoiceField(
        label='Półka',
        queryset=Shelf.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    category = forms.ModelChoiceField(
        label='Kategoria',
        queryset=Category.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    include_expired = forms.BooleanField(
        label='Uwzględnij przedmioty przeterminowane',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )
    include_removed = forms.BooleanField(
        label='Uwzględnij przedmioty usunięte',
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
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


class CustomUserCreationForm(UserCreationForm):
    """Custom form for user registration with optional email"""

    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        help_text='Opcjonalny. Wprowadź adres email, aby móc się zalogować używając go zamiast nazwy użytkownika.',
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add bootstrap classes to password fields
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('Użytkownik o tej nazwie już istnieje.')
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Użytkownik o tym adresie email już istnieje.')
        return email
