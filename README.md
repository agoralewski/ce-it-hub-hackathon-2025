# KSP - Krwinkowy System Prezentowy

KSP (Krwinkowy System Prezentowy) is an inventory management system (IMS) developed for CE Tech Hub Hackathon 2025. The application is designed to manage warehouse items with specific requirements for a foundation's storage system.

## Features

- User authentication system with admin and standard user roles
- Warehouse organization with rooms, racks, and shelves
- Item tracking with categories, expiration dates, and location
- Mobile-responsive interface for easy inventory management
- QR code generation for quick access to shelf information
- Excel export functionality for inventory reports
- Email notifications for expiring items
- Multiple language support (Polish and English)

## Requirements

- Python 3.8 or higher
- Django 5.0 or higher
- Additional dependencies listed in `requirements.txt`

## Quick Start Guide

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/ce-it-hub-hackathon-2025.git
cd ce-it-hub-hackathon-2025
```

### 2. Set up a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example environment file and update it with your settings:

```bash
cp .env.example .env
```

Edit the `.env` file with your specific configuration:
- Set a secure `SECRET_KEY`
- Configure email settings for password reset functionality

### 5. Set up the database

```bash
python manage.py migrate
```

### 6. Create a superuser (admin account)

```bash
python manage.py createsuperuser
```

### 7. Run the development server

```bash
python manage.py runserver
```

The application will be available at http://127.0.0.1:8000/

### 8. Access the admin interface

Visit http://127.0.0.1:8000/admin/ and log in with the superuser credentials.

## Project Structure

- `warehouse/` - Main application for inventory management
- `ksp/` - Project settings
- `static/` - Static files (CSS, JS, images)
- `templates/` - HTML templates
- `media/` - User-uploaded files (created when needed)

## User Types

1. **Warehouse Administrator**:
   - Full access to all application features
   - Can manage warehouse structure (rooms, racks, shelves)
   - Can create/manage item categories

2. **Regular User**:
   - Can view the inventory
   - Can add/remove items from shelves
   - Can filter and search for items

## Deployment

For production deployment:

1. Set `DEBUG=False` in your environment
2. Configure the `ALLOWED_HOSTS` setting
3. Use a production-grade web server (e.g., Gunicorn, uWSGI)
4. Set up a reverse proxy (e.g., Nginx)

## License

MIT License

## Acknowledgements

Developed for CE Tech Hub Hackathon 2025.