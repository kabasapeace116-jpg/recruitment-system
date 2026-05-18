import sys
import os

# Set the path to your Django project
INTERP = "/home/yourusername/python/bin/python3"

# Check if the interpreter exists
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

# Add your project directory to the path
sys.path.append(os.getcwd())
sys.path.append('/home/yourusername/django_project')

# Set Django settings module
os.environ['DJANGO_SETTINGS_MODULE'] = 'recruitment_system.settings'

# Load the Django app
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()