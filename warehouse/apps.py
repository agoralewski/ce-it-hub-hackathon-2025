from django.apps import AppConfig
from django.conf import settings


class WarehouseConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'warehouse'
    
    def ready(self):
        # Import and start the scheduler only if not in a management command
        # This prevents duplicate scheduler initialization
        import sys
        if settings.DEBUG and ('runserver' in sys.argv or 'uvicorn' in sys.argv):
            self.start_scheduler()
        elif not settings.DEBUG and 'gunicorn' in sys.argv[0]:
            self.start_scheduler()
            
    def start_scheduler(self):
        from warehouse.scheduler import start_scheduler
        start_scheduler()
