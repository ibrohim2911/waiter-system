import requests
import os
import subprocess
import time
import sys

# Change these to your actual URLs
VERSION_CHECK_URL = "https://github.com/ibrohim2911/waiter-system/blob/main/version.json"
LATEST_EXE_URL = "https://github.com/waiter.exe"
CURRENT_VERSION = "1.0.0" 

def update():
    try:
        # 1. Check version
        r = requests.get(VERSION_CHECK_URL, timeout=5)
        latest_version = r.json().get("version")

        if latest_version > CURRENT_VERSION:
            print(f"Updating to {latest_version}...")
            
            # 2. Download new version as a temporary file
            new_content = requests.get(LATEST_EXE_URL).content
            with open("waiter_new.tmp", "wb") as f:
                f.write(new_content)

            # 3. Create the "Swapper" Batch file
            # This script waits for waiter.exe to close, deletes it, and renames the new one
            with open("swap.bat", "w") as f:
                f.write(f"""
                @echo off
                taskkill /f /im waiter.exe >nul 2>&1
                timeout /t 2 /nobreak > nul
                del waiter.exe
                ren waiter_new.tmp waiter.exe
                start waiter.exe
                del swap.bat
                """)
            
            # 4. Run the swapper and exit
            subprocess.Popen("swap.bat", shell=True)
            sys.exit()
            
    except Exception as e:
        print(f"Update failed: {e}")

if __name__ == "__main__":
    update()