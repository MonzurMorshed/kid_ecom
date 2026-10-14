import os
import sys

# Set up paths so that project modules and apps are easily discoverable
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

APPS_DIR = os.path.join(CURRENT_DIR, 'apps')
if APPS_DIR not in sys.path:
    sys.path.insert(0, APPS_DIR)

# Configure Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kidurabd.settings')

# Import WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
