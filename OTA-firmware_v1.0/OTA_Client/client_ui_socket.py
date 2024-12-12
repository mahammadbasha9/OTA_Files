import tkinter as tk
from tkinter import messagebox, scrolledtext
import subprocess
import os
import stat
import platform

# Define your file paths
RECEIVED_FILE_PATH = "/OTA/Delta_packages/received.patch"
UPDATED_FILE_PATH = "/OTA/Current_Versions/my_current"
UPDATED_PATH = "/OTA/Current_Versions/hello_updated"

def execute_bspatch(root, action):
    try:
        if action == "current_version":
            # Check if file exists
            if os.path.isfile(UPDATED_FILE_PATH):
                # Execute the executable and capture output
                output = execute_executable(UPDATED_FILE_PATH)
                if output:
                    open_current_version_gui(root, output)
                else:
                    messagebox.showerror("Error", "Empty output received from executable.")
            else:
                messagebox.showerror("Error", f"File not found: {UPDATED_FILE_PATH}")

        elif action == "apply_patch":
            # Check if received patch file exists
            if not os.path.isfile(RECEIVED_FILE_PATH):
                messagebox.showerror("Error", f"Patch file not found: {RECEIVED_FILE_PATH}")
                return

            # Check if original file exists
            if not os.path.isfile(UPDATED_FILE_PATH):
                messagebox.showerror("Error", f"Original file not found: {UPDATED_FILE_PATH}")
                return

            # Check file size of original file
            updated_file_size = os.path.getsize(UPDATED_FILE_PATH)
           #print(f"Original file size: {updated_file_size} bytes")

            if updated_file_size == 0:
                messagebox.showerror("Error", f"Original file is empty: {UPDATED_FILE_PATH}")
                return

            # Construct the bspatch command
            command = ["bspatch", UPDATED_FILE_PATH, UPDATED_PATH, RECEIVED_FILE_PATH]
           #print(f"Executing command: {' '.join(command)}")

            # Execute the command
            result = subprocess.run(command, capture_output=True, text=True)

            if result.returncode == 0:
                messagebox.showinfo("bspatch Successful", "bspatch command executed successfully.")
                os.chmod(UPDATED_PATH, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)  # Give execute permission
            else:
                messagebox.showerror("bspatch Failed", f"Error executing bspatch command: {result.stderr}")

        elif action == "demo_update":
            # Check if demo executable exists
            if os.path.isfile(UPDATED_PATH):
                # Execute the demo executable and capture output
                output = execute_executable(UPDATED_PATH)
                if output:
                    open_demo_gui(root, output)
                else:
                    messagebox.showerror("Error", "Empty output received from demo executable.")
            else:
                messagebox.showerror("Error", f"Demo executable not found: {UPDATED_PATH}")

        else:
            messagebox.showerror("Error", "Unknown action requested.")

    except FileNotFoundError as e:
        messagebox.showerror("File Error", f"File not found: {e.filename}")
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Execution Error", f"Error executing command: {e}")
    except Exception as e:
        messagebox.showerror("Error", f"Unexpected error: {e}")

def execute_executable(executable_path):
    try:
        # Execute the executable and capture output
        result = subprocess.run([executable_path], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()  # Strip trailing newline characters
        else:
            return f"Error executing {executable_path}: {result.stderr.strip()}"
    except Exception as e:
        return f"Exception occurred: {e}"

def open_demo_gui(root, content):
    # Create a new window for demo GUI
    demo_window = tk.Toplevel(root)
    demo_window.title("Executable Output")
    demo_window.geometry("600x250")  # Reduced height to 250 pixels

    try:
        # Display output content
        text_area = tk.Text(demo_window, wrap=tk.NONE, height=10)
        text_area.insert(tk.END, content)
        text_area.config(state=tk.DISABLED)  # Make text widget read-only
        text_area.pack(padx=20, pady=15)

        ok_button = tk.Button(demo_window, text="OK", command=demo_window.destroy)
        ok_button.pack(pady=10)

        # Focus back on the main window after closing demo window
        root.focus_force()

    except Exception as e:
        messagebox.showerror("Error", f"Error displaying content: {e}")
        demo_window.destroy()

def open_current_version_gui(root, content):
    # Create a new window for current version GUI
    current_version_window = tk.Toplevel(root)
    current_version_window.title("Current Version Output")
    current_version_window.geometry("600x250")  # Reduced height to 250 pixels

    try:
        # Display output content
        text_area = tk.Text(current_version_window, wrap=tk.NONE, height=10)
        text_area.insert(tk.END, content)
        text_area.config(state=tk.DISABLED)  # Make text widget read-only
        text_area.pack(padx=20, pady=15)

        # OK button to close the current version window
        ok_button = tk.Button(current_version_window, text="OK", command=current_version_window.destroy)
        ok_button.pack(pady=10)

        # Focus back on the main window after closing current version window
        root.focus_force()

    except Exception as e:
        messagebox.showerror("Error", f"Error displaying content: {e}")
        current_version_window.destroy()

def open_file(filepath):
    try:
        if platform.system() == "Linux":
            subprocess.Popen([filepath])
        elif platform.system() == "Windows":
            os.startfile(filepath)  # Use os.startfile on Windows
        else:
            messagebox.showerror("Error", "Unsupported platform")
    except Exception as e:
        messagebox.showerror("Error", f"Error opening file: {e}")

def open_gui():
    root = tk.Tk()
    root.title("Client GUI")
    root.geometry("400x300")
    root.configure(background="light grey")

    label_font = ("Arial", 14)
    button_font = ("Arial", 14)
    label_fg_color = "#800080"
    button_fg_color = "white"
    button_bg_color = "green"

    label = tk.Label(root, text="DEMO UPDATES", font=("Arial", 14, "bold"), fg=label_fg_color)
    label.pack(pady=10)

    current_version_button = tk.Button(root, text="Current Version", font=button_font, fg=button_fg_color, bg=button_bg_color, command=lambda: execute_bspatch(root, "current_version"))
    current_version_button.pack(pady=20)

    apply_patch_button = tk.Button(root, text="Apply bspatch", font=button_font, fg=button_fg_color, bg=button_bg_color, command=lambda: execute_bspatch(root, "apply_patch"))
    apply_patch_button.pack(pady=20)

    demo_update_button = tk.Button(root, text="Demo Update", font=button_font, fg=button_fg_color, bg=button_bg_color, command=lambda: execute_bspatch(root, "demo_update"))
    demo_update_button.pack(pady=20)

    root.mainloop()

if __name__ == "__main__":
    open_gui()
