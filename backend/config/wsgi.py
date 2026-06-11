import os
import sys

# Ensure Django uses the correct virtual environment
VENV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".venv"))
if VENV_PATH not in sys.path:
    sys.path.insert(0, VENV_PATH)

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
application = get_wsgi_application()
