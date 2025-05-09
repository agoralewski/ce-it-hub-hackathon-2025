from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from warehouse.models import Room, Rack, Shelf, Category, Item, ItemShelfAssignment
from django.utils import timezone
from datetime import timedelta
import random

class Command(BaseCommand):
    help = 'Creates sample data for testing the KSP system'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating sample data for KSP...')
        
        # Create superuser if it doesn't exist
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'adminpassword')
            self.stdout.write(self.style.SUCCESS('Superuser created: admin/adminpassword'))
        
        # Create rooms
        rooms = []
        room_names = ['Sala główna', 'Magazyn A', 'Magazyn B', 'Pomieszczenie techniczne']
        for name in room_names:
            room, created = Room.objects.get_or_create(name=name)
            rooms.append(room)
            if created:
                self.stdout.write(f'Created room: {name}')
        
        # Create racks
        racks = []
        for room in rooms:
            for i in range(1, 4):  # 3 racks per room
                rack_name = f"Regał {i} - {room.name}"
                rack, created = Rack.objects.get_or_create(name=rack_name, room=room)
                racks.append(rack)
                if created:
                    self.stdout.write(f'Created rack: {rack_name}')
        
        # Create shelves
        shelves = []
        for rack in racks:
            for i in range(1, 6):  # 5 shelves per rack
                shelf_name = f"Półka {i} - {rack.name}"
                shelf, created = Shelf.objects.get_or_create(
                    name=shelf_name,
                    rack=rack,
                    qr_code_uuid=None  # QR code will be generated automatically in the model
                )
                shelves.append(shelf)
                if created:
                    self.stdout.write(f'Created shelf: {shelf_name}')
        
        # Create categories
        categories = []
        category_names = ['Elektronika', 'Zabawki', 'Książki', 'Ubrania', 'Artykuły szkolne']
        for name in category_names:
            category, created = Category.objects.get_or_create(name=name)
            categories.append(category)
            if created:
                self.stdout.write(f'Created category: {name}')
        
        # Create items
        items = []
        item_data = [
            {'name': 'Laptop Dell', 'category': 'Elektronika', 'description': 'Laptop Dell Inspiron 15', 'manufacturer': 'Dell'},
            {'name': 'Myszka komputerowa', 'category': 'Elektronika', 'description': 'Bezprzewodowa myszka Logitech', 'manufacturer': 'Logitech'},
            {'name': 'Klocki Lego', 'category': 'Zabawki', 'description': 'Zestaw klocków Lego City', 'manufacturer': 'Lego'},
            {'name': 'Miś pluszowy', 'category': 'Zabawki', 'description': 'Duży pluszowy miś', 'manufacturer': 'TeddyToys'},
            {'name': 'Harry Potter', 'category': 'Książki', 'description': 'Książka Harry Potter i Kamień Filozoficzny', 'manufacturer': 'Media Rodzina'},
            {'name': 'Pan Tadeusz', 'category': 'Książki', 'description': 'Lektura szkolna', 'manufacturer': 'Ossolineum'},
            {'name': 'Bluza', 'category': 'Ubrania', 'description': 'Ciepła bluza z kapturem', 'manufacturer': 'Nike'},
            {'name': 'Kurtka zimowa', 'category': 'Ubrania', 'description': 'Zimowa kurtka dla dziecka', 'manufacturer': 'Columbia'},
            {'name': 'Zeszyt A4', 'category': 'Artykuły szkolne', 'description': 'Zeszyt 80 kartek w kratkę', 'manufacturer': 'Oxford'},
            {'name': 'Długopisy', 'category': 'Artykuły szkolne', 'description': 'Zestaw 10 kolorowych długopisów', 'manufacturer': 'Bic'}
        ]
        
        for item_info in item_data:
            # Get the right category
            category = next((c for c in categories if c.name == item_info['category']), categories[0])
            
            # Random expiration date between 1 month and 2 years from now
            days_to_add = random.randint(30, 730)
            expiration_date = timezone.now().date() + timedelta(days=days_to_add)
            
            item, created = Item.objects.get_or_create(
                name=item_info['name'],
                defaults={
                    'category': category,
                    'description': item_info['description'],
                    'manufacturer': item_info['manufacturer'],
                    'expiration_date': expiration_date,
                    'quantity': random.randint(1, 10),
                    'donor': f"Darczyńca {random.randint(1, 20)}"
                }
            )
            items.append(item)
            if created:
                self.stdout.write(f'Created item: {item.name}')
        
        # Create item-shelf assignments
        for item in items:
            # Random shelf assignment
            for _ in range(random.randint(1, 3)):  # Assign each item to 1-3 shelves
                shelf = random.choice(shelves)
                quantity_on_shelf = random.randint(1, item.quantity)
                
                assignment, created = ItemShelfAssignment.objects.get_or_create(
                    item=item,
                    shelf=shelf,
                    defaults={
                        'quantity': quantity_on_shelf
                    }
                )
                if created:
                    self.stdout.write(f'Assigned {quantity_on_shelf} of {item.name} to {shelf.name}')
        
        self.stdout.write(self.style.SUCCESS('Successfully created sample data'))
