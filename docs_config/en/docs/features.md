---
hide:
  - navigation
---

### System Architecture

The system consists of the following components:

1. **Django Web Application** - The main backend application serving dynamic content via Gunicorn
2. **PostgreSQL Database** - Stores all application data
3. **Nginx** - Reverse proxy that handles HTTP requests, static file serving, and routing

### Key features
- User authentication with admin and standard user roles
- Warehouse organization with rooms, racks, and shelves
- Item tracking with categories, expiration dates, and location
- Mobile-responsive interface for easy inventory management
- QR code generation for quick access to shelf information
- Excel export functionality for inventory reports
- Email notifications for expiring items and password reset
- Multiple language support (Polish and English)

### Networking Setup

The application is, as requested, only available on local network, so no https, domains, or certificates are issued for it.  
Mobile devices connecting to the application need to be connected to the same network as the host.

### User Types

1. **Warehouse Administrator**:  
   -Full access to all application features  
   -Can manage warehouse structure (rooms, racks, shelves)  
   -Can manage item categories  
   -Can export to excel  
   -Can view history of item movements (removals, additions)

2. **Regular User**:  
   -Can view the inventory  
   -Can add/remove items from shelves  
   -Can filter and search for items
