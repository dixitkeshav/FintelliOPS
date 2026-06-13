#!/usr/bin/env python
import os
import sys

# Ensure Django uses the correct virtual environment
VENV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".venv"))
if VENV_PATH not in sys.path:
    sys.path.insert(0, VENV_PATH)

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
