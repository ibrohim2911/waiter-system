#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
        
        # --- ADD THIS SECTION ---
        # If the app is running as a built EXE and starts the server
        if 'runserver' in sys.argv:
            print("Checking for database updates...")
            # This runs 'python manage.py migrate' automatically
            execute_from_command_line(['manage.py', 'migrate', '--noinput'])
            print("Database is up to date.")
        # -------------------------

    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)
if __name__ == '__main__':
    main()