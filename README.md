# KSP - Krwinkowy System Prezentowy

KSP (Krwinkowy System Prezentowy) is an inventory management system (IMS) developed for CE Tech Hub Hackathon 2025. The application is designed to manage warehouse items with specific requirements for a charity's storage system.

## Features

- User authentication with admin and standard user roles
- Warehouse organization with rooms, racks, and shelves
- Item tracking with categories, expiration dates, and location
- Mobile-responsive interface for easy inventory management
- QR code generation for quick access to shelf information
- Excel export functionality for inventory reports
- Email notifications for expiring items and password reset
- Multiple language support (Polish and English)

## Requirements

- Docker compose for deployment
- Python > 3.12 & UV package manager for local development

## Quick Start
```bash
git clone https://github.com/yourusername/ce-it-hub-hackathon-2025.git hackathon25
cd hackathon25
uv sync
cp .env.example .env
#optional: set DEBUG=True in .env
./scripts/set_network_ip.sh
docker compose up -d
./scripts/manage_django.sh
```

## Project Structure

- `warehouse/` - Main application for inventory management
- `ksp/` - Project settings
- `static/` - Static files (CSS, JS, images)
- `templates/` - HTML templates
- `locale/` - Translation files for multi-language support
- `docs/` - MKdocs markdown files

## live documentation: 
[Mkdocs on Github Pages](https://agoralewski.github.io/ce-it-hub-hackathon-2025/)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

Developed for CE Tech Hub Hackathon 2025.