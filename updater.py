import requests
import os
import subprocess
import time
import sys

# CONFIGURATION
VERSION_URL = "https://raw.githubusercontent.com/ibrohim2911/waiter-system/main/version.json"
# This URL should point to the direct download of your new .exe
EXE_URL = "https://github.com/ibrohim2911/waiter-system/releases/latest/download/RestaurantServer.exe"
LOCAL_VERSION = "1.0.0" 
MAIN_EXE_NAME = "RestaurantServer.exe"

def run_update():
    try:
        # 1. Check for updates
        r = requests.get(VERSION_URL, timeout=10)
        remote_version = r.json().get("version")

        if remote_version > LOCAL_VERSION:
            print(f"New version {remote_version} detected. downloading...")
            
            # 2. Download new version to a temp file
            response = requests.get(EXE_URL, stream=True)
            temp_file = "RestaurantServer_new.tmp"
            
            with open(temp_file, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            # 3. Create the Swap script
            # We use a .bat because Windows won't let us delete an EXE while it's running
            with open("update_swap.bat", "w") as f:
                f.write(f"""
                @echo off
                echo Waiting for application to close...
                timeout /t 5 /nobreak > nul
                taskkill /f /im {MAIN_EXE_NAME} >nul 2>&1
                del "{MAIN_EXE_NAME}"
                ren "{temp_file}" "{MAIN_EXE_NAME}"
                start "" "{MAIN_EXE_NAME}"
                del "update_swap.bat"
                """)
            
            # 4. Launch the swap script and kill the updater
            subprocess.Popen(["update_swap.bat"], shell=True)
            sys.exit()
            
    except Exception as e:
        print(f"Update check skipped: {e}")

if __name__ == "__main__":
    # Wait 15 seconds after waiter opens the app to check for updates
    time.sleep(15)
    run_update()