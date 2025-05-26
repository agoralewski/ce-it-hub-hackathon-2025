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
        label='Liczba',
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


class ItemLocationForm(ItemShelfAssignmentForm):
    """Form for adding items with location selection"""

    room = forms.ModelChoiceField(
        label='Pokój',
        queryset=Room.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control room-select'}),
        required=True,
    )

    rack = forms.ModelChoiceField(
        label='Regał',
        queryset=Rack.objects.none(),  # Initially empty, will be populated by JavaScript
        widget=forms.Select(attrs={'class': 'form-control rack-select'}),
        required=True,
    )

    shelf = forms.ModelChoiceField(
        label='Półka',
        queryset=Shelf.objects.none(),  # Initially empty, will be populated by JavaScript
        widget=forms.Select(attrs={'class': 'form-control shelf-select'}),
        required=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # If room is provided in POST data, populate rack queryset
        if 'room' in self.data:
            try:
                room_id = int(self.data.get('room'))
                self.fields['rack'].queryset = Rack.objects.filter(
                    room_id=room_id
                ).order_by('name')
            except (ValueError, TypeError):
                pass
        # If room is provided in initial data, also populate rack queryset
        elif self.initial.get('room'):
            try:
                room_id = int(self.initial.get('room'))
                self.fields['rack'].queryset = Rack.objects.filter(
                    room_id=room_id
                ).order_by('name')
            except (ValueError, TypeError):
                pass

        # If rack is provided in POST data, populate shelf queryset
        if 'rack' in self.data:
            try:
                rack_id = int(self.data.get('rack'))
                self.fields['shelf'].queryset = Shelf.objects.filter(
                    rack_id=rack_id
                ).order_by('number')
            except (ValueError, TypeError):
                pass
        # If rack is provided in initial data, also populate shelf queryset
        elif self.initial.get('rack'):
            try:
                rack_id = int(self.initial.get('rack'))
                self.fields['shelf'].queryset = Shelf.objects.filter(
                    rack_id=rack_id
                ).order_by('number')
            except (ValueError, TypeError):
                pass


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
        queryset=Rack.objects.none(),  # Start with empty queryset
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    shelf = forms.ModelChoiceField(
        label='Półka',
        queryset=Shelf.objects.none(),  # Start with empty queryset
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

        # Always start with all rooms sorted by name
        self.fields['room'].queryset = Room.objects.all().order_by('name')

        # Filter racks based on selected room
        if args and 'room' in args[0] and args[0]['room']:
            room_id = args[0]['room']
            self.fields['rack'].queryset = Rack.objects.filter(
                room_id=room_id
            ).order_by('name')

            # If a rack is selected, populate shelves for that rack
            if 'rack' in args[0] and args[0]['rack']:
                rack_id = args[0]['rack']
                self.fields['shelf'].queryset = Shelf.objects.filter(
                    rack_id=rack_id
                ).order_by('number')

        # For GET requests (initial display)
        initial_data = kwargs.get('initial', {})
        if 'room' in initial_data and initial_data['room']:
            room_id = initial_data['room']
            self.fields['rack'].queryset = Rack.objects.filter(
                room_id=room_id
            ).order_by('name')

            if 'rack' in initial_data and initial_data['rack']:
                rack_id = initial_data['rack']
                self.fields['shelf'].queryset = Shelf.objects.filter(
                    rack_id=rack_id
                ).order_by('number')


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


class UserProfileForm(forms.ModelForm):
    """Form for editing user profile information"""

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make fields that might be null required in the form
        self.fields['email'].required = True

    def clean_username(self):
        username = self.cleaned_data.get('username')
        # Check if username exists but isn't the current user's username
        if (
            User.objects.filter(username__iexact=username)
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            raise forms.ValidationError('Użytkownik o tej nazwie już istnieje.')
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Check if email exists but isn't the current user's email
        if (
            email
            and User.objects.filter(email__iexact=email)
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            raise forms.ValidationError('Użytkownik o tym adresie email już istnieje.')
        return email
