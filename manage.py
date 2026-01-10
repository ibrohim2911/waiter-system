#!/usr/bin/env python
import os
import sys
import subprocess
from waitress import serve  # <--- 1. Import Waitress

def main():
    """Run administrative tasks."""
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    
    # 2. Import the WSGI application (must happen AFTER setting settings path)
    from django.core.management import execute_from_command_line
    from config.wsgi import application 

    # If running as an EXE (frozen), run migrations automatically before starting server
    if getattr(sys, 'frozen', False) and len(sys.argv) == 1:
        print("Checking database migrations...")
        execute_from_command_line(['manage.py', 'migrate', '--noinput'])

    # Standard run logic
    if len(sys.argv) == 1:
        # --- 3. REPLACED RUNSERVER WITH WAITRESS ---
        print("Starting Waitress Production Server...")
        print("Serving on http://0.0.0.0:8000 with 10 threads")
        
        # 'threads=10' ensures your 7 users can click at the same time without crashing
        serve(application, host='0.0.0.0', port=8000, threads=10)
    else:
        # Keep this so you can still run 'createsuperuser' or 'shell' if needed
        execute_from_command_line(sys.argv)
    
if __name__ == '__main__':
    main()