import tkinter as tk
from tkinter import messagebox, ttk
import requests
import os
import subprocess
import zipfile
import io
import threading
import json
import sys

# --- DYNAMIC PATH CALCULATION ---
if getattr(sys, 'frozen', False):
    LAUNCHER_DIR = os.path.dirname(sys.executable)
else:
    LAUNCHER_DIR = os.path.dirname(os.path.abspath(__file__))

# Move up to the parent directory where RestaurantPOS lives
BASE_DIR = os.path.dirname(LAUNCHER_DIR)
APP_FOLDER = os.path.join(BASE_DIR, "RestaurantPOS")
SERVER_EXE = "RestaurantServer.exe"
EXE_PATH = os.path.join(APP_FOLDER, SERVER_EXE)
SETTINGS_FILE = os.path.join(APP_FOLDER, "launcher_settings.json")

FULL_PACKAGE_URL = "https://github.com/ibrohim2911/waiter-system/releases/latest/download/RestaurantPOS.zip"

class RestaurantLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("Restaurant POS Launcher")
        self.root.geometry("450x450")

        tk.Label(root, text="Restaurant POS System", font=("Arial", 18, "bold")).pack(pady=10)
        
        # --- API SETTINGS ---
        settings_frame = tk.LabelFrame(root, text="Connection Settings", padx=10, pady=10)
        settings_frame.pack(pady=10, fill="x", padx=20)
        tk.Label(settings_frame, text="Server API URL:").grid(row=0, column=0, sticky="w")
        self.api_url_entry = tk.Entry(settings_frame, width=30)
        self.api_url_entry.grid(row=0, column=1, padx=5)
        
        self.load_current_config()

        # --- UI CONTROLS ---
        self.status_lbl = tk.Label(root, text="Checking status...", fg="gray")
        self.status_lbl.pack()
        self.progress = ttk.Progressbar(root, orient="horizontal", length=350, mode="determinate")
        self.progress.pack(pady=15)
        self.btn_main = tk.Button(root, text="Please Wait", state="disabled", width=25, height=2, 
                                 font=("Arial", 10, "bold"), command=self.handle_button_click)
        self.btn_main.pack(pady=5)

        self.tools_frame = tk.Frame(root)
        self.tools_frame.pack(pady=10)
        tk.Button(self.tools_frame, text="Repair DB", command=self.repair_db, width=12).grid(row=0, column=0, padx=5)
        tk.Button(self.tools_frame, text="Create Admin", command=self.create_admin, width=12).grid(row=0, column=1, padx=5)
        tk.Button(self.tools_frame, text="Clear Print Queue", command=self.clear_print_queue, width=15).grid(row=0, column=2, padx=5)

        self.refresh_ui()

    def clear_print_queue(self, silent=False):
        if not silent and not messagebox.askyesno("Confirm", "Are you sure you want to clear all pending print jobs?"):
            return

        # We need to load the config to get the URL
        self.load_current_config()
        api_url = self.api_url_entry.get().strip()
        if not api_url:
            if not silent:
                messagebox.showerror("Error", "Server API URL cannot be empty.")
            else:
                print("Error: Server API URL not configured.")
            return

        # Ensure we're targeting the right endpoint
        clear_url = f"{api_url.rstrip('/')}/api/order/clear-print-queue/"

        try:
            response = requests.get(clear_url, timeout=10)
            response.raise_for_status() # Raise an exception for bad status codes
            
            data = response.json()
            message = data.get("message", "Print queue cleared successfully!")
            if not silent:
                messagebox.showinfo("Success", message)
            else:
                print(message)

        except requests.exceptions.RequestException as e:
            if not silent:
                messagebox.showerror("Request Error", f"Could not connect to the server: {e}")
            else:
                print(f"Request Error: Could not connect to the server: {e}")
        except Exception as e:
            if not silent:
                messagebox.showerror("Error", f"An unexpected error occurred: {e}")
            else:
                print(f"An unexpected error occurred: {e}")

    def load_current_config(self):
        """Loads from /MySoftwareRoot/RestaurantPOS/launcher_settings.json"""
        default_url = "http://localhost:8000"
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r") as f:
                    data = json.load(f)
                    default_url = data.get("API_URL", default_url)
            except: pass
        self.api_url_entry.delete(0, tk.END)
        self.api_url_entry.insert(0, default_url)

    def save_config(self):
        """Saves to /MySoftwareRoot/RestaurantPOS/launcher_settings.json"""
        api_url = self.api_url_entry.get().strip()
        try:
            os.makedirs(APP_FOLDER, exist_ok=True)
            with open(SETTINGS_FILE, "w") as f:
                json.dump({"API_URL": api_url}, f)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Could not save settings: {e}")
            return False

    def refresh_ui(self):
        if os.path.exists(EXE_PATH):
            self.status_lbl.config(text="Ready to Launch", fg="green")
            self.btn_main.config(text="LAUNCH SERVER", state="normal", bg="#4CAF50", fg="white")
            self.progress['value'] = 100
            self.tools_frame.pack()
        else:
            self.status_lbl.config(text="App not installed", fg="red")
            self.btn_main.config(text="DOWNLOAD & INSTALL", state="normal", bg="#2196F3", fg="white")
            self.progress['value'] = 0
            self.tools_frame.pack_forget()

    def launch_app(self):
        if self.save_config():
            try:
                subprocess.Popen([EXE_PATH], cwd=APP_FOLDER)
                subprocess.Popen(
                    [EXE_PATH, "run_printer"], 
                    cwd=APP_FOLDER,
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
                self.root.destroy()
            except Exception as e:
                messagebox.showerror("Launch Error", f"Failed to start: {e}")
    def handle_button_click(self):
        if self.btn_main['text'] == "LAUNCH SERVER":
            self.launch_app()
        else:
            self.start_download()

    def start_download(self):
        self.btn_main.config(state="disabled", text="Downloading...")
        threading.Thread(target=self.download_logic, daemon=True).start()

    def download_logic(self):
        try:
            r = requests.get(FULL_PACKAGE_URL, stream=True, timeout=15)
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            data = io.BytesIO()
            downloaded = 0
            for chunk in r.iter_content(chunk_size=1024*1024):
                if chunk:
                    data.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        self.root.after(0, lambda p=percent: self.update_progress(p))

            self.root.after(0, lambda: self.status_lbl.config(text="Extracting...", fg="orange"))
            
            # Extract into the PARENT folder so RestaurantPOS folder is created there
            with zipfile.ZipFile(data) as z:
                z.extractall(BASE_DIR)
            
            self.root.after(0, self.refresh_ui)
            self.root.after(0, lambda: messagebox.showinfo("Success", "Installation Complete!"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Download Failed: {str(e)}"))
            self.root.after(0, self.refresh_ui)

    def update_progress(self, val):
        self.progress['value'] = val

    def repair_db(self):
        if messagebox.askyesno("Confirm", "Run database migrations?"):
            subprocess.run([EXE_PATH, "migrate"], cwd=APP_FOLDER, shell=True)
            messagebox.showinfo("Done", "Migrations completed.")

    def create_admin(self):
        # Open cmd in the RestaurantPOS directory
        cmd = f'start cmd /k "cd /d {APP_FOLDER} && {SERVER_EXE} createsuperuser"'
        os.system(cmd)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == 'clear-print-queue':
        # Create a dummy root window to access the launcher methods, but don't show it.
        root = tk.Tk()
        root.withdraw()
        app = RestaurantLauncher(root)
        app.clear_print_queue(silent=True)
    else:
        root = tk.Tk()
        app = RestaurantLauncher(root)
        root.mainloop()