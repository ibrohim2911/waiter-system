
#!/usr/bin/env python
import os
import sys
import subprocess # <--- Add this

def main():
    """Run administrative tasks."""
    
    # --- UPDATER TRIGGER START ---
    # This checks if updater.exe exists in the same folder as the running app
    if getattr(sys, 'frozen', False):
        # We are running as a compiled .exe
        current_dir = os.path.dirname(sys.executable)
    else:
        # We are running in a normal python environment
        current_dir = os.path.dirname(os.path.abspath(__file__))

    updater_path = os.path.join(current_dir, "updater.exe")
    
    # Launch updater.exe silently if it exists
    if os.path.exists(updater_path):
        try:
            # CREATE_NO_WINDOW ensures no black box pops up for the waiter
            subprocess.Popen([updater_path], creationflags=0x08000000) 
        except Exception:
            pass 
    # --- UPDATER TRIGGER END ---

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'waiter_system.settings')
    from django.core.management import execute_from_command_line

    # If running as an EXE (frozen), run migrations automatically before starting server
    if getattr(sys, 'frozen', False) and len(sys.argv) == 1:
        print("Checking database migrations...")
        execute_from_command_line(['manage.py', 'migrate', '--noinput'])

    # Standard run logic
    if len(sys.argv) == 1:
        execute_from_command_line(['manage.py', 'runserver', '0.0.0.0:8000', '--noreload'])
    else:
        execute_from_command_line(sys.argv)
if __name__ == '__main__':
    main()

