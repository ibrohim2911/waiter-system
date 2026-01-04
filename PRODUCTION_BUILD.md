# Waiter System - PyInstaller Embedded Deployment Guide

This guide explains how to build and deploy your Waiter System as a standalone `.exe` using PyInstaller.

## Overview

The "embedded" approach bundles:
- **Django backend** (REST API)
- **React frontend** (bundled into static files)
- **SQLite database** (zero installation, single file)

Result: A single `Restaurant.exe` that users click to run. No Docker, no background services, no installation.

---

## Prerequisites

1. **Python 3.8+** (installed and in PATH)
2. **Node.js & npm** (for building React frontend)
3. **PyInstaller**: `pip install pyinstaller` (or it's in requirements.txt)
4. **Frontend folder location**: `./frontend/` (in the waiter-system root)
   - Your React app should have `package.json` and a build script configured

---

## Step 1: Prepare the Frontend

Ensure your React frontend is in `./frontend/` and configured to build:

```bash
cd frontend
npm install
npm run build
cd ..
```

The React build output should go to `frontend/dist/` (Vite/Create React App default).

If your build output is elsewhere, update the `frontend_build` path in `waiter.spec`.

---

## Step 2: Prepare the Backend

Install Python dependencies:

```bash
pipenv install
# OR if using pip directly:
pip install -r requirements.txt
```

Run migrations to ensure your SQLite database is set up:

```bash
python manage.py migrate
python manage.py createsuperuser  # Optional: create admin user
```

If you plan to use Django's database-backed caching, create the cache table before building:

```bash
python manage.py createcachetable django_cache
```

If you want client-side assets to be served with long-lived cache headers (recommended), the project uses WhiteNoise to serve static files with hashed filenames. Ensure you run `collectstatic` before building so hashed static filenames are produced:

```bash
python manage.py collectstatic --noinput
```

---

## Step 3: Build the Executable

### On Windows (PowerShell or CMD):

```bash
build.bat
```

Or manually:

```bash
python manage.py collectstatic --noinput
cd frontend && npm run build && cd ..
pyinstaller waiter.spec
```

### On macOS/Linux:

```bash
bash build.sh
```

**Output**: The `.exe` (or app bundle) will be in `dist/Restaurant/`

---

## Step 4: Run the Application

Double-click:
```
dist/Restaurant/Restaurant.exe
```

Or from PowerShell:
```bash
.\dist\Restaurant\Restaurant.exe
```

The app will:
1. Start the Django development server on `http://localhost:8000`
2. Serve the React frontend
3. Open your browser automatically (optional—can be added to launcher)

---

## Troubleshooting

### Issue: `frontend` folder not found
- Ensure your React app is at `./frontend/` relative to the waiter-system root
- Update `waiter.spec` if your folder is named differently

### Issue: React build missing
- Run `cd frontend && npm run build && cd ..` before `pyinstaller`
- Check that `frontend/dist/` exists

### Issue: SQLite database not included
- The build script automatically includes `db.sqlite3` if it exists
- If you need to reset the DB after bundling, delete `db.sqlite3` and run `python manage.py migrate` before rebuilding

### Issue: Static files not loading
- Ensure `python manage.py collectstatic --noinput` runs successfully before building
- Check `config/settings.py` for correct `STATIC_ROOT` and `STATICFILES_DIRS` paths

---

## Advanced: Auto-Launch Browser

To automatically open the browser when the `.exe` starts, create a launcher script:

**`launcher.py`**:
```python
import os
import subprocess
import webbrowser
import time
import sys

def main():
    # Start Django server in background
    django_process = subprocess.Popen(
        [sys.executable, 'manage.py', 'runserver', '127.0.0.1:8000'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for server to start
    time.sleep(2)
    
    # Open browser
    webbrowser.open('http://localhost:8000')
    
    # Keep process alive
    django_process.wait()

if __name__ == '__main__':
    main()
```

Then update `waiter.spec` to use `launcher.py` instead of `manage.py`.

---

## Production Notes

- **Secret Key**: Keep the SECRET_KEY in `config/settings.py` unique and secure
- **DEBUG**: Automatically set to `False` when running as `.exe` (see settings.py)
- **Database**: SQLite is sufficient for single-restaurant deployments. For multi-location, consider Postgres
- **Icon**: Place an `icon.ico` file in the project root and the build will use it

---

## File Structure

```
waiter-system/
├── manage.py
├── db.sqlite3
├── requirements.txt
├── build.bat                 # Windows build script
├── build.sh                  # macOS/Linux build script
├── waiter.spec               # PyInstaller spec file
├── config/
│   └── settings.py           # Updated for PyInstaller
├── frontend/                 # React app (MUST exist)
│   ├── package.json
│   ├── src/
│   └── dist/                 # Built React files (after npm run build)
├── staticfiles/              # Collected Django static files
├── user/, order/, inventory/, log/
└── dist/                     # Output folder (after build)
    └── Restaurant/
        └── Restaurant.exe    # Final executable
```

---

## FAQ

**Q: Do users need Python installed?**  
A: No. The .exe is standalone.

**Q: Can they run multiple instances?**  
A: Not with the default setup (port 8000 conflict). Modify the server startup to use a dynamic port if needed.

**Q: How do I update the app?**  
A: Rebuild the .exe and redistribute `dist/Restaurant/Restaurant.exe` to users.

**Q: Can I add a custom icon?**  
A: Yes, place an `icon.ico` file in the project root. The build script already references it.

---

## Next Steps

1. Move your React app to `./frontend/` if it isn't already
2. Run `npm run build` to test the frontend build
3. Run `build.bat` (Windows) or `bash build.sh` (macOS/Linux)
4. Test `dist/Restaurant/Restaurant.exe`

Good luck! 🚀
