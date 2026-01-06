import tkinter as tk
from tkinter import messagebox, ttk
import requests
import os
import sys
import subprocess
import zipfile
import io
import threading

# --- CONFIGURATION ---
# The ZIP must contain the full 'RestaurantPOS' folder content (_internal + exe)
FULL_PACKAGE_URL = "https://github.com/ibrohim2911/waiter-system/releases/latest/download/RestaurantPOS.zip"
VERSION_URL = "https://raw.githubusercontent.com/ibrohim2911/waiter-system/main/version.json"
SERVER_EXE = "RestaurantServer.exe"
CURRENT_VERSION = "0.0.0" # Default for launcher; it checks local file for real version

class Bootstrapper:
    def __init__(self, root):
        self.root = root
        self.root.title("Waiter System Installer")
        self.root.geometry("400x250")
        
        tk.Label(root, text="Restaurant System Launcher", font=("Arial", 16, "bold")).pack(pady=15)
        
        self.status_lbl = tk.Label(root, text="Checking installation...", fg="gray")
        self.status_lbl.pack(pady=5)

        self.progress = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")
        self.progress.pack(pady=20)

        self.btn_action = tk.Button(root, text="Wait...", state="disabled", width=20, height=2, command=self.launch_app)
        self.btn_action.pack(pady=10)

        # Check automatically on start
        self.root.after(1000, self.check_installation)

    def check_installation(self):
        """Checks if the main app exists. If not, prompts install."""
        if os.path.exists(SERVER_EXE):
            self.status_lbl.config(text="Ready to launch", fg="green")
            self.btn_action.config(text="LAUNCH APP", state="normal", bg="#4CAF50", fg="white")
            self.progress['value'] = 100
        else:
            self.status_lbl.config(text="App not found.", fg="red")
            self.btn_action.config(text="DOWNLOAD & INSTALL", state="normal", bg="#2196F3", fg="white", command=self.start_download)

    def start_download(self):
        self.btn_action.config(state="disabled")
        threading.Thread(target=self.download_and_extract).start()

    def download_and_extract(self):
        try:
            self.status_lbl.config(text="Downloading full package...", fg="blue")
            
            # 1. Download ZIP
            response = requests.get(FULL_PACKAGE_URL, stream=True)
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            data = io.BytesIO()
            
            for chunk in response.iter_content(chunk_size=1024*1024): # 1MB chunks
                if chunk:
                    data.write(chunk)
                    downloaded += len(chunk)
                    # Update Progress Bar
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        self.root.after(0, lambda p=percent: self.update_progress(p))

            self.status_lbl.config(text="Extracting files...", fg="orange")
            
            # 2. Extract ZIP
            with zipfile.ZipFile(data) as z:
                z.extractall(".") # Extract to current directory
            
            self.root.after(0, self.install_complete)

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            self.root.after(0, lambda: self.btn_action.config(state="normal"))

    def update_progress(self, val):
        self.progress['value'] = val

    def install_complete(self):
        self.status_lbl.config(text="Installation Complete!", fg="green")
        self.progress['value'] = 100
        self.btn_action.config(text="LAUNCH APP", state="normal", bg="#4CAF50", command=self.launch_app)
        messagebox.showinfo("Success", "Installation finished successfully.")

    def launch_app(self):
        if os.path.exists(SERVER_EXE):
            subprocess.Popen([SERVER_EXE])
            self.root.destroy()
        else:
            messagebox.showerror("Error", "Executable missing!")

if __name__ == "__main__":
    root = tk.Tk()
    app = Bootstrapper(root)
    root.mainloop()