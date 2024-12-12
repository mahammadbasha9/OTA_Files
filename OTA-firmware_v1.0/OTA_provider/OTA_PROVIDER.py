
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.font import Font
from PIL import Image, ImageTk
import hashlib
import re
import json
import os
import time
import ctypes
import threading
import subprocess



# Paths to the JSON files where user credentials will be stored
USER_CREDENTIALS_FILE = "user_credentials.json"


def load_json(file_path):
    """Load JSON data from a file, return an empty dictionary if file does not exist or is empty."""
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        with open(file_path, 'r') as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                return {}
    return {}

def save_json(data, file_path):
    """Save JSON data to a file."""
    with open(file_path, 'w') as file:
        json.dump(data, file)

# Load existing user credentials (username and hashed password)
user_credentials = load_json(USER_CREDENTIALS_FILE)

def get_version_info(system_name):
    folder_path = f"/OTA/{system_name}/current_versions"
    if os.path.exists(folder_path):
        files = os.listdir(folder_path)
        if files:
            # Get the latest file
            latest_file = max(files, key=lambda f: os.path.getmtime(os.path.join(folder_path, f)))
            # Extract version and last updated time
            version = latest_file.split(' ')[0]  # Assuming the version is the filename without extension
            last_updated = time.strftime('%a %b %d %H:%M:%S %Y', time.localtime(os.path.getmtime(os.path.join(folder_path, latest_file))))
            return version, last_updated
    return "N/A", "N/A"

def open_new_page():
    new_window = tk.Toplevel(root)
    new_window.title("Eximietas Rsync configuration")
    new_window.geometry("1365x768")
    new_window.configure(bg='#f2f2f2')

    def on_new_window_close():
        new_window.destroy()
        root.destroy()

    new_window.protocol("WM_DELETE_WINDOW", on_new_window_close)

    # Create a frame to act as the box for the label
    label_frame = tk.Frame(new_window, bg='purple', bd=2, relief="solid")
    label_frame.pack(pady=20, padx=20, fill="x")

    # Add a label to the label_frame
    label = tk.Label(label_frame, text="Eximietas Rsync configuration", font=('Helvetica', 18, 'bold'), bg='purple', fg='white')
    label.pack(pady=20, padx=20)

    # Create a frame to act as the box for the buttons
    button_frame = tk.Frame(new_window, bg='purple', bd=2, relief="solid")
    button_frame.pack(pady=20, padx=20, fill="both", expand=True)

    # Add buttons to the button_frame using grid
# Correcting the function name in the button command
    button_sw_version = tk.Button(button_frame, text="SW Version", font=('Helvetica', 16, 'bold'), bg='purple', fg='white', width=25, height=3, command=open_sw_versions_page)

    button_sw_version.grid(row=0, column=0, padx=(20, 10), pady=10, sticky="w")

    button_ota_server = tk.Button(button_frame, text="OTA Server", font=('Helvetica', 16, 'bold'), bg='purple', fg='white', width=25, height=3)

    button_ota_server.grid(row=0, column=1, padx=10, pady=10, sticky="w")

    button_security = tk.Button(button_frame, text="Security", font=('Helvetica', 16, 'bold'), bg='purple', fg='white', width=25, height=3, command=show_security)
    button_security.grid(row=0, column=2, padx=10, pady=10, sticky="w")

    button_about = tk.Button(button_frame, text="About", font=('Helvetica', 16, 'bold'), bg='purple', fg='white', width=25, height=3, command=show_about)
    button_about.grid(row=0, column=3, padx=(10, 20), pady=10, sticky="w")

    # Configure row and column weights to make the content expand when the window is resized
    button_frame.grid_rowconfigure(0, weight=1)
    button_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

    # Create a frame to act as the box for the table
    table_outer_frame = tk.Frame(new_window, bg='purple', bd=2, relief="solid")
    table_outer_frame.pack(pady=20, padx=20, fill="both", expand=True)

    # Create a table with 4 rows and 3 columns
    table_frame = tk.Frame(table_outer_frame, bg='purple')
    table_frame.pack(pady=20, padx=20)

    # Manually add content to each cell with the first row having a purple background
    cell_content = [
            ["Systems", "Current SW Version", "Last Updated"],
            ["Cars", *get_version_info("Cars")],
            ["Mobiles", *get_version_info("Mobiles")],
            ["IOT", *get_version_info("IOT")]
            ]

    for row in range(4):
        for column in range(3):
            bg_color = 'gray' if row == 0 else 'white'  # Change background color of headers to black
            fg_color = 'white' if row == 0 else 'black'
            cell = tk.Label(table_frame, text=cell_content[row][column], bg=bg_color, fg=fg_color, borderwidth=1, relief="solid", width=30, height=3, font=('Helvetica', 14))
            cell.grid(row=row, column=column, padx=5, pady=5)
    # Configure row and column weights to make the content expand when the window is resized
    table_outer_frame.grid_rowconfigure(0, weight=1)
    table_outer_frame.grid_columnconfigure(0, weight=1)
def show_about():
    messagebox.showinfo("About", "Remote Sync by Eximietas Design Ver1.0")
def show_security():
    messagebox.showinfo("security", "Coming Soon         ")

#sw_page

def center_window(window, width, height):
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")

def populate_versions(tree, current_folder, sw_folder):
    for item in tree.get_children():
        tree.delete(item)

    try:
        current_versions = []
        sw_versions = []

        # Get current versions
        if os.path.exists(current_folder):
            current_versions = os.listdir(current_folder)
            current_versions.sort()

        # Get SW versions
        if os.path.exists(sw_folder):
            sw_versions = os.listdir(sw_folder)
            sw_versions.sort()

        # Highlight the current versions in a special color
        for version in current_versions:
            tree.insert("", "end", values=(version, "Current"), tags=("current",))

        # Add SW versions
        for version in sw_versions:
            if version not in current_versions:
                tree.insert("", "end", values=(version, "Available"), tags=("available",))

        # Highlight the first current version
        if current_versions:
            first_current_item = tree.get_children()[0]
            tree.item(first_current_item, tags=("highlight",))

    except FileNotFoundError:
        tree.insert("", "end", values=("No versions found", ""), tags=("error",))

def on_version_select(event, tree):
    selected_items = tree.selection()
    if selected_items:
        selected_item = selected_items[0]
        # Proceed with your logic for handling the selected item
    else:
        # Handle case where no item is selected
        pass
ip_after_id = None
port_after_id = None
def open_sw_versions_page():
    global ip_var, ip_entry, ip_after_id, port_var, port_entry, port_after_id, clients, tree, radio_frame, new_client_var, new_ip_var, new_status_var, new_client_frame

    def clear_entry(event, entry, default_text):
        if entry.get() == default_text:
            entry.delete(0, tk.END)
            entry.config(foreground='black')
    def is_valid_ip(ip):
        return re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip) is not None

    def is_valid_port(port):
        return port.isdigit() and 0 <= int(port) <= 65535
    def reset_entry(event, var, default_text):
        if not var.get():
            var.set(default_text)
            event.widget.config(foreground='grey')

    def schedule_ip_validation(event):
        global ip_after_id
        if ip_after_id:
            root.after_cancel(ip_after_id)
        ip_after_id = root.after(2000, validate_ip)

    def validate_ip():
        ip = ip_var.get()
        if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip):
            ip_var.set("IP Address")
            ip_entry.config(foreground='grey')
        else:
            ip_entry.config(foreground='black')

    def schedule_port_validation(event):
        global port_after_id
        if port_after_id:
            root.after_cancel(port_after_id)
        port_after_id = root.after(2000, validate_port)

    def validate_port():
        port = port_var.get()
        if not port.isdigit() or not (0 <= int(port) <= 65535):
            port_var.set("Port")
            port_entry.config(foreground='grey')
        else:
            port_entry.config(foreground='black')
    def update_versions():
        selected_item = None
        selected_tree = None
        for tree in [car_tree, mobile_tree, iot_tree]:
            selected_items = tree.selection()
            if selected_items:
                selected_item = selected_items[0]
                selected_tree = tree
                break

        if selected_item and selected_tree:
            version = selected_tree.item(selected_item, "values")[0]
            base_folder = ""
            current_version_folder = ""
            patch_folder = ""
            #patch_folder = "/OTA/Delta_packages"

            if selected_tree == car_tree:
                base_folder = "/OTA/Cars/sw_versions"
                patch_folder = "/OTA/Cars/Delta_packages"
                current_version_folder = "/OTA/Cars/current_versions"
            elif selected_tree == mobile_tree:
                base_folder = "/OTA/Mobiles/sw_versions"
                patch_folder = "/OTA/Mobiles/Delta_packages"
                current_version_folder = "/OTA/Mobiles/current_versions"
            elif selected_tree == iot_tree:
                base_folder = "/OTA/IOT/sw_versions"
                patch_folder = "/OTA/IOT/Delta_packages"
                current_version_folder = "/OTA/IOT/current_versions"
            else:
                messagebox.showerror("Invalid Selection", "Please select a valid version.")
                return

            current_version_dir = os.path.join(current_version_folder)
            current_version_subfolders = [f.path for f in os.scandir(current_version_dir) if f.is_dir()]

            if not current_version_subfolders:
                messagebox.showerror("Folder Error", f"No versions found in the current version folder: {current_version_dir}")
                return

            current_version_folder_path = current_version_subfolders[0]
            current_a_out_file = os.path.join(current_version_folder_path, "current")

            selected_folder_path = os.path.join(base_folder, version)
            selected_a_out_file = os.path.join(selected_folder_path, "new")

            if not os.path.isfile(current_a_out_file):
                messagebox.showerror("File Error", f"The file {current_a_out_file} does not exist.")
                return
            if not os.path.isfile(selected_a_out_file):
                messagebox.showerror("File Error", f"The file {selected_a_out_file} does not exist.")
                return

            patch_file = os.path.join(patch_folder, f"{version}.patch")
            bsdiff_command = ["bsdiff", current_a_out_file, selected_a_out_file, patch_file]
            try:
                subprocess.run(bsdiff_command, check=True)
                messagebox.showinfo("Patch Created", f"Patch file created successfully: {patch_file}")
            except subprocess.CalledProcessError as e:
                messagebox.showerror("Patch Error", f"Failed to create patch file: {e}")

        else:
            messagebox.showerror("No Version Selected", "Please select a version to update.")

    def push_versions():
        ip_address = ip_var.get()
        port_number = port_var.get()

        if not is_valid_ip(ip_address):
            messagebox.showerror("Invalid IP", "Please enter a valid IP address.")
            return

        if not is_valid_port(port_number):
            messagebox.showerror("Invalid Port", "Please enter a valid port number (0-65535).")
            return

        selected_item = None
        selected_tree = None
        for tree in [car_tree, mobile_tree, iot_tree]:
            selected_items = tree.selection()
            if selected_items:
                selected_item = selected_items[0]
                selected_tree = tree
                break

        if selected_item and selected_tree:
            version = selected_tree.item(selected_item, "values")[0]
            base_folder = ""

            if selected_tree == car_tree:
                base_folder = "/OTA/Cars/Delta_packages"
                device_name = "Cars"
            elif selected_tree == mobile_tree:
                base_folder = "/OTA/Mobiles/Delta_packages"
                device_name = "Mobiles"
            elif selected_tree == iot_tree:
                base_folder = "/OTA/IOT/Delta_packages"
                device_name = "IOT"
            else:
                messagebox.showerror("Invalid Selection", "Please select a valid version.")
                return

            patch_file_name = f"{version}.patch"
            patch_file_path = os.path.join(base_folder, patch_file_name)

            if not os.path.isfile(patch_file_path):
                messagebox.showerror("Patch File Error", f"The patch file {patch_file_path} does not exist.")
                return

            client_command = ["./client1", ip_address, port_number, device_name, patch_file_path]
            try:
                subprocess.run(client_command, check=True)
                messagebox.showinfo("Push", f"Patch file {patch_file_name} has been pushed to {ip_address}:{port_number}")
            except subprocess.CalledProcessError as e:
                messagebox.showerror("Client Error", f"Failed to push patch file {patch_file_name}: {e}")
        else:
            messagebox.showerror("No Version Selected", "Please select a version to push.")

    def on_version_double_click(event, tree):
        selected_item = tree.selection()
        if selected_item:
            tree.selection_remove(selected_item)

    sw_window = tk.Toplevel(root)
    sw_window.title("SW Version Management")
    sw_window.update_versions = update_versions

    window_width = 1365
    window_height = 850
    center_window(sw_window, window_width, window_height)

    sw_window.configure(bg='#ffffff')

    title_label = tk.Label(sw_window, text="SW Version Management", font=("Helvetica", 16), bg='#800080', fg='#ffffff')
    title_label.pack(fill="x", padx=10, pady=(10, 0), ipady=10)

    input_frame = tk.Frame(sw_window)
    input_frame.pack(pady=10)

    button_width = 20
    button_height = 2
    button_padx = 10
    button_pady = 5
    button_bg = "#9A4EAE"
    button_fg = "white"
    button_relief = "raised"

    max_button_width = max(len("OTA Provider Address"), len("IP Address"), len("Port")) + 2

    sw_provider_button = tk.Button(input_frame, text="SW Provider Address", width=max_button_width, bg=button_bg, fg=button_fg, relief=button_relief)
    sw_provider_button.grid(row=0, column=0, padx=button_padx, pady=button_pady)

    ip_var = tk.StringVar()
    ip_var.set("IP Address")
    ip_entry = ttk.Entry(input_frame, textvariable=ip_var, font=("Arial", 14), width=25)
    ip_entry.grid(row=0, column=1, padx=(120, 10), pady=5, sticky="ew")  # Adjusted padx for more right alignment

    port_var = tk.StringVar()
    port_var.set("Port")
    port_entry = ttk.Entry(input_frame, textvariable=port_var, font=("Arial", 14), width=20)
    port_entry.grid(row=0, column=8, padx=(120, 150), pady=5, sticky="ew")  # Adjusted padx for more right alignment

    ip_entry.bind("<FocusIn>", lambda event: clear_entry(event, ip_entry, "IP Address"))
    ip_entry.bind("<FocusOut>", lambda event: reset_entry(event, ip_var, "IP Address"))
    ip_entry.bind("<KeyRelease>", schedule_ip_validation)

    port_entry.bind("<FocusIn>", lambda event: clear_entry(event, port_entry, "Port"))
    port_entry.bind("<FocusOut>", lambda event: reset_entry(event, port_var, "Port"))
    port_entry.bind("<KeyRelease>", schedule_port_validation)



    style = ttk.Style()
    style.configure("Treeview", rowheight=25)
    style.configure("Treeview.Heading", font=("Helvetica", 10, "bold"))
    style.map("Treeview", background=[("selected", "#800080")])

    script_dir = os.path.dirname(os.path.abspath(__file__))
    current_versions_folder_cars = os.path.join(script_dir, "/OTA/Cars/current_versions/")
    sw_versions_folder_cars = os.path.join(script_dir, "/OTA/Cars/sw_versions/")

    car_frame = tk.Frame(sw_window, bg='#E6E6FA')
    car_frame.pack(pady=10)

    car_label = tk.Label(car_frame, text="Cars", font=("Helvetica", 14, "bold"), bg='#f0f0f0', fg='#800080')
    car_label.grid(row=0, column=0, padx=10)

    car_tree = ttk.Treeview(car_frame, columns=("Version", "Status"), show="headings", height=7)
    car_tree.heading("Version", text="Version")
    car_tree.heading("Status", text="Status")
    car_tree.column("Version", anchor="center", width=200)
    car_tree.column("Status", anchor="center", width=100)
    car_tree.grid(row=1, column=0, padx=10)

    car_tree.tag_configure("current", background="#FFA07A")  # Light Salmon for current versions
    car_tree.tag_configure("highlight", background="#FFD700")  # Gold for the first current version
    car_tree.tag_configure("available", background="white")  # White for available versions
    car_tree.tag_configure("selected", background="#800080", foreground="white")  # Purple for selected item

    car_tree.bind("<<TreeviewSelect>>", lambda event: on_version_select(event, car_tree))
    car_update_button = tk.Button(car_frame, text="Update", command=update_versions, width=button_width, bg=button_bg, fg=button_fg, relief=button_relief)
    car_update_button.grid(row=1, column=1, padx=button_padx, pady=button_pady)






    car_push_button = tk.Button(car_frame, text="Push", command=push_versions, width=button_width, bg=button_bg, fg=button_fg, relief=button_relief)
    car_push_button.grid(row=1, column=2, padx=button_padx, pady=button_pady)

    car_tree.bind("<Double-1>", lambda event: on_version_double_click(event, car_tree))

    #for version in os.listdir(sw_versions_folder_cars):
     #   car_tree.insert("", tk.END, values=(version,))

    current_versions_folder_mobile = os.path.join(script_dir, "/OTA/Mobiles/current_versions")
    sw_versions_folder_mobile = os.path.join(script_dir, "/OTA/Mobiles/sw_versions/")

    mobile_frame = tk.Frame(sw_window, bg='#E6E6FA')
    mobile_frame.pack(pady=10)

    mobile_label = tk.Label(mobile_frame, text="Mobile", font=("Helvetica", 14, "bold"), bg='#f0f0f0', fg='#800080')
    mobile_label.grid(row=0, column=0, padx=10)

    mobile_tree = ttk.Treeview(mobile_frame, columns=("Version", "Status"), show="headings", height=7)
    mobile_tree.heading("Version", text="Version")
    mobile_tree.heading("Status", text="Status")
    mobile_tree.column("Version", anchor="center", width=200)
    mobile_tree.column("Status", anchor="center", width=100)
    mobile_tree.grid(row=1, column=0, padx=10)

    mobile_tree.tag_configure("current", background="#FFA07A")  # Light Salmon for current versions
    mobile_tree.tag_configure("highlight", background="#FFD700")  # Gold for the first current version
    mobile_tree.tag_configure("available", background="white")  # White for available versions
    mobile_tree.tag_configure("selected", background="#800080", foreground="white")  # Purple for selected item

    mobile_tree.bind("<<TreeviewSelect>>", lambda event: on_version_select(event, mobile_tree))

    mobile_update_button = tk.Button(mobile_frame, text="Update", command=update_versions, width=button_width, bg=button_bg, fg=button_fg, relief=button_relief)
    mobile_update_button.grid(row=1, column=1, padx=button_padx, pady=button_pady)



    mobile_push_button = tk.Button(mobile_frame, text="Push", command=push_versions, width=button_width, bg=button_bg, fg=button_fg, relief=button_relief)
    mobile_push_button.grid(row=1, column=2, padx=button_padx, pady=button_pady)


    mobile_tree.bind("<Double-1>", lambda event: on_version_double_click(event, mobile_tree))

    #for version in os.listdir(sw_versions_folder_mobiles):
     #   mobile_tree.insert("", tk.END, values=(version,))

    current_versions_folder_iot = os.path.join(script_dir, "/OTA/IOT/current_versions/")
    sw_versions_folder_iot = os.path.join(script_dir, "/OTA/IOT/sw_versions/")

    iot_frame = tk.Frame(sw_window, bg='#E6E6FA')
    iot_frame.pack(pady=10)

    iot_label = tk.Label(iot_frame, text="IOT", font=("Helvetica", 14, "bold"), bg='#f0f0f0', fg='#800080')
    iot_label.grid(row=0, column=0, padx=10)

    iot_tree = ttk.Treeview(iot_frame, columns=("Version", "Status"), show="headings", height=7)
    iot_tree.heading("Version", text="Version")
    iot_tree.heading("Status", text="Status")
    iot_tree.column("Version", anchor="center", width=200)
    iot_tree.column("Status", anchor="center", width=100)
    iot_tree.grid(row=1, column=0, padx=10)

    iot_tree.tag_configure("current", background="#FFA07A")  # Light Salmon for current versions
    iot_tree.tag_configure("highlight", background="#FFD700")  # Gold for the first current version
    iot_tree.tag_configure("available", background="white")  # White for available versions
    iot_tree.tag_configure("selected", background="#800080", foreground="white")  # Purple for selected item

    iot_tree.bind("<<TreeviewSelect>>", lambda event: on_version_select(event, iot_tree))
    iot_tree.bind("<Double-1>", lambda event: on_version_double_click(event, iot_tree))

    #for version in os.listdir(sw_versions_folder_iot):
     #   iot_tree.insert("", tk.END, values=(version,))

    iot_update_button = tk.Button(iot_frame, text="Update", command=update_versions, width=button_width, bg=button_bg, fg=button_fg, relief=button_relief)
    iot_update_button.grid(row=1, column=1, padx=button_padx, pady=button_pady)

    iot_push_button = tk.Button(iot_frame, text="Push", command=push_versions, width=button_width, bg=button_bg, fg=button_fg, relief=button_relief)
    iot_push_button.grid(row=1, column=2, padx=button_padx, pady=button_pady)

    back_button = tk.Button(sw_window, text="Back", bg='#800080', fg='white', command=sw_window.destroy)
    back_button.place(relx=1.0, rely=1.0, anchor='se')

    # Populate the treeviews with versions
    populate_versions(car_tree, current_versions_folder_cars, sw_versions_folder_cars)
    populate_versions(mobile_tree, current_versions_folder_mobile, sw_versions_folder_mobile)
    populate_versions(iot_tree, current_versions_folder_iot, sw_versions_folder_iot)







def update_client_status(index, status):
    clients[index]['Status'] = status
    save_client_configurations("client_configurations.txt")
    update_treeview()

def save_client_configurations(filename):
    with open(filename, 'w') as file:
        for client in clients:
            line = f"{client['Client']},{client['IP Address']},{client['Status']}\n"
            file.write(line)

def read_client_configurations(filename):
    global clients
    clients = load_client_configurations(filename)
    update_treeview()

def load_client_configurations(filename):
    if not os.path.exists(filename):
        return []

    clients = []
    with open(filename, 'r') as file:
        for line in file:
            client_data = line.strip().split(',')
            if len(client_data) == 3:
                client = {
                        "Client": client_data[0],
                        "IP Address": client_data[1],
                        "Status": client_data[2]
                        }
                clients.append(client)
    return clients






def open_signup_page():
    new_window = tk.Toplevel(root)
    new_window.title("Signup")
    new_window.geometry("1365x768")
    new_window.configure(bg='#f2f2f2')

    def resize_image(event):
        new_width = event.width
        new_height = event.height
        image = bg_image.resize((new_width, new_height), Image.LANCZOS)
        background_image = ImageTk.PhotoImage(image)
        canvas.create_image(0, 0, image=background_image, anchor="nw")
        canvas.image = background_image  # Keep a reference to avoid garbage collection

        # Update font size and widget sizes based on the new dimensions
        scale = new_width / 1365
        font_size = int(14 * scale)
        custom_font.config(size=font_size)
        button_width = int(15 * scale)
        button_height = int(2 * scale)

        button_register.config(width=button_width, height=button_height, font=custom_font)

    canvas = tk.Canvas(new_window)
    canvas.pack(fill="both", expand=True)
    canvas.bind("<Configure>", resize_image)
    canvas.create_image(0, 0, image=background_image, anchor="nw")

    custom_font = Font(family="Helvetica", size=14)

    label_username_signup = tk.Label(new_window, text="New Username", bg='white', font=custom_font)
    entry_username_signup = tk.Entry(new_window, width=30, font=custom_font)

    label_password_signup = tk.Label(new_window, text="New Password", bg='white', font=custom_font)
    entry_password_signup = tk.Entry(new_window, show='*', width=30, font=custom_font)

    label_confirm_password_signup = tk.Label(new_window, text="Confirm Password", bg='white', font=custom_font)
    entry_confirm_password_signup = tk.Entry(new_window, show='*', width=30, font=custom_font)

    label_password_criteria = tk.Label(new_window, text="Password must contain at least one special character, one number,\n and one uppercase letter.", bg='white', font=custom_font)

    button_register = tk.Button(new_window, text="Register", command=lambda: register(new_window, entry_username_signup.get(), entry_password_signup.get(), entry_confirm_password_signup.get()), bg='#800080', fg='#fff', width=15, height=2, font=custom_font)

    x_offset = 0.58
    y_offset = 0.35

    label_username_signup.place(relx=x_offset, rely=y_offset, anchor="nw")
    entry_username_signup.place(relx=x_offset + 0.15, rely=y_offset, anchor="nw")
    label_password_signup.place(relx=x_offset, rely=y_offset + 0.05, anchor="nw")
    entry_password_signup.place(relx=x_offset + 0.15, rely=y_offset + 0.05, anchor="nw")
    label_confirm_password_signup.place(relx=x_offset, rely=y_offset + 0.1, anchor="nw")
    entry_confirm_password_signup.place(relx=x_offset + 0.15, rely=y_offset + 0.1, anchor="nw")
    label_password_criteria.place(relx=x_offset, rely=y_offset + 0.15, anchor="nw")
    button_register.place(relx=x_offset + 0.10, rely=y_offset + 0.25, anchor="nw")

def login():
    username = entry_username.get()
    password = hashlib.sha256(entry_password.get().encode()).hexdigest()

    if username in user_credentials and user_credentials[username] == password:
        messagebox.showinfo("Login", "Login Successful")
        root.withdraw()  # Hide the main login window

        # Open the new page only if root existed (root.withdraw() was successful)
        if tk._default_root:  # Check if the default root still exists
            open_new_page()
    else:
        if messagebox.askyesno("Login Failed", "User not found. Do you want to register?"):
            open_signup_page()
        entry_username.delete(0, 'end')  # Clear the username entry
        entry_password.delete(0, 'end')  # Clear the password entry

def register(window, username, password, confirm_password):
    if len(user_credentials) >= 5:
        messagebox.showerror("Register", "User limit reached. Cannot register more users.", parent=window)
        return
    if not re.match(r'^(?=.*[A-Z])(?=.*\d)(?=.*\W)', password):
        messagebox.showerror("Register", "Password must contain at least one special character, one number, and one uppercase letter.", parent=window)
    elif password != confirm_password:
        messagebox.showerror("Register", "Passwords do not match.", parent=window)
    elif username in user_credentials:
        messagebox.showerror("Register", "Username already exists.", parent=window)
    else:
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        user_credentials[username] = hashed_password
        save_json(user_credentials, USER_CREDENTIALS_FILE)
        messagebox.showinfo("Register", "Registration Successful", parent=window)
        window.destroy()

def resize_image(event):
    new_width = event.width
    new_height = event.height
    image = bg_image.resize((new_width, new_height), Image.LANCZOS)
    background_image = ImageTk.PhotoImage(image)
    canvas.create_image(0, 0, image=background_image, anchor="nw")
    canvas.image = background_image  # Keep a reference to avoid garbage collection

    # Update font size and widget sizes based on the new dimensions
    scale = new_width / 1365
    font_size = int(14 * scale)
    custom_font.config(size=font_size)
    button_width = int(15 * scale)
    button_height = int(2 * scale)

    button_login.config(width=button_width, height=button_height, font=custom_font)
    button_signup.config(width=button_width, height=button_height, font=custom_font)

root = tk.Tk()
root.title("Login Page")
root.geometry("1365x768")

bg_image = Image.open("logo.jpg")

canvas = tk.Canvas(root)
canvas.pack(fill="both", expand=True)
canvas.bind("<Configure>", resize_image)
background_image = ImageTk.PhotoImage(bg_image)
canvas.create_image(0, 0, image=background_image, anchor="nw")

custom_font = Font(family="Helvetica", size=14)

label_username = tk.Label(root, text="Username", bg='white', font=custom_font)
entry_username = tk.Entry(root, width=30, font=custom_font)

label_password = tk.Label(root, text="Password", bg='white', font=custom_font)
entry_password = tk.Entry(root, show='*', width=30, font=custom_font)

button_login = tk.Button(root, text="Login", command=login, bg='#800080', fg='#fff', width=15, height=2, font=custom_font)

button_signup = tk.Button(root, text="Signup", command=open_signup_page, bg='#800080', fg='#fff', width=15, height=2, font=custom_font)

emoji_label = tk.Label(root, bg='#f2f2f2')

x_offset = 0.58
y_offset = 0.35

label_username.place(relx=x_offset, rely=y_offset, anchor="nw")
entry_username.place(relx=x_offset + 0.1, rely=y_offset, anchor="nw")
label_password.place(relx=x_offset, rely=y_offset + 0.05, anchor="nw")
entry_password.place(relx=x_offset + 0.1, rely=y_offset + 0.05, anchor="nw")
button_login.place(relx=x_offset + 0.025, rely=y_offset + 0.1, anchor="nw")
button_signup.place(relx=x_offset + 0.2, rely=y_offset + 0.1, anchor="nw")

root.mainloop()

