import os
import json
import paho.mqtt.client as mqtt
import warnings
import threading
import logging

# Set up logging to file
logging.basicConfig(
    level=logging.INFO,  # Set the log level
    format='%(levelname)s - %(message)s',  # Log message format
    handlers=[logging.FileHandler('Ota_server.log', mode='a'),  # Write logs to 'app.log' file (append mode)
              logging.StreamHandler()]  # Optionally, log to console as well
)

warnings.filterwarnings("ignore", category=DeprecationWarning)

# Server Configuration
Server_Version = "1.2"  # Server's firmware version
device_details_file = "device_info.json"
latest_file_path = "/OTA/Delta_packages/firmware_v1.1.bin"  # Path to the latest firmware file
topic_device_version = "metadata/version"  # Topic to receive version info
topic_file_transfer = "File/Transfer/{client_ip}"  # Topic for transferring the firmware file
topic_device_ack = "File/Ack/#"  # Topic to receive acknowledgments

# Thread-safe tracking for clients
selected_clients_lock = threading.Lock() # Lock to ensure thread-safe access to selected clients
selected_clients = set()  # Clients selected for processing
processed_versions = {}  # To track processed client versions
acknowledgment_pending = set()  # Clients waiting for acknowledgment

"""
    This function saves the given device details to a JSON file.
    If the file already exists, it will load the existing data,
    update it with the new device details, and save it back to the file."""
def save_device_details(device_details):
    try:
        # Check if the file already exists
        if os.path.exists(device_details_file):
            # Read the existing data
            with open(device_details_file, "r") as file:
                existing_data = json.load(file)
        else:
            existing_data = {}

        # Update the dictionary with the new device details
        existing_data.update(device_details)

        # Write the updated data to the JSON file
        with open(device_details_file, "w") as file:
            json.dump(existing_data, file, indent=4)
        logging.info(f"Device details saved to {device_details_file}")
    except Exception as e:
        logging.error(f"Error saving device details: {e}")

""" Reset all states for handling a new batch of clients.
    This function is responsible for clearing the states associated with 
    client processing to prepare for a new batch. It ensures thread-safe 
    operations by acquiring a lock before modifying shared resources."""
def reset_states():
    global selected_clients, processed_versions, acknowledgment_pending
    with selected_clients_lock:
        selected_clients.clear()  # Clear the previous list of selected clients
        processed_versions.clear()  # Reset version tracking
        acknowledgment_pending.clear()  # Clear acknowledgment tracking
    logging.info("Reset states for new clients.")

""" Load selected clients from an environment variable.
    This function retrieves the list of selected clients from the 
    "SELECTED_CLIENTS" environment variable and updates the global 
    `selected_clients` variable. The operation is performed within a 
    thread-safe block using a lock."""
def load_selected_clients():
    """Load selected clients from environment variable."""
    global selected_clients
    with selected_clients_lock:
        selected_clients = os.getenv("SELECTED_CLIENTS", "").split(",")
        logging.info(f"Loaded Selected Clients: {selected_clients}")

""" Update `validate_client` to dynamically reload `selected_clients`
    Validate if a client is eligible for processing.
    This function checks if a given client ID exists in the list of selected 
    clients or the acknowledgment pending list. It ensures thread-safe access 
    to the `selected_clients` list using a lock."""
def validate_client(client_id):
    """Check if the client is in the selected clients or pending acknowledgment list."""
    global selected_clients
    #load_selected_clients()  # Reload selected clients dynamically
    logging.info(f"Current Selected Clients Publisher side: {selected_clients}")

    with selected_clients_lock:
        if client_id in selected_clients or client_id in acknowledgment_pending:
            logging.info(f"Client {client_id} is valid for processing.")
            return True
        else:
            logging.info(f"Client {client_id} is not valid for processing. Ignoring.")
            return False

""" Compare the client's version with the server's version and determine the update status.
    This function checks the relationship between the version reported by a client and 
    the version on the server. It uses a thread-safe approach to ensure consistent 
    access to the `processed_versions` dictionary"""
def compare_versions(client_id, received_version, server_version):
    with selected_clients_lock:
        if processed_versions.get(client_id) == received_version:
            logging.info(f"Client {client_id}: Version {received_version} already processed. Ignoring.")
            return "processed"

        if received_version == server_version:
            logging.info(f"Client {client_id}: Versions match. No update needed.")
            return "match"
        elif received_version < server_version:
            logging.info(f"Client {client_id}: Version {received_version} is outdated. Preparing to send update...")
            processed_versions[client_id] = received_version
            return "outdated"
        else:
            logging.info(f"Client {client_id}: Version {received_version} is newer than the server version. Check for inconsistencies.")
            return "inconsistent"

""" Handle and process acknowledgment messages received from clients.
    This function processes an acknowledgment payload sent by a client to confirm 
    the successful receipt of an update. It validates the payload format, extracts 
    the necessary details, and updates the acknowledgment tracking accordingly."""
def process_acknowledgment(payload):
    try:
        if 'IP Address' in payload and 'File Size' in payload:
            parts = payload.split(', ')
            ip_address = parts[0].replace('IP Address: ', '').strip()
            file_size = parts[1].replace('File Size: ', '').replace(' bytes', '').strip()
            
            with selected_clients_lock:
                if ip_address not in acknowledgment_pending:
                    logging.info(f"Acknowledgment from {ip_address} is unexpected or duplicate. Ignoring.")
                    return
                
                acknowledgment_pending.remove(ip_address)  # Remove client from pending acknowledgments
                logging.info(f"Acknowledgment Received: IP Address: {ip_address}, File Size: {file_size} bytes")
                reset_states()
        else:
            logging.error(f"Error: Unexpected acknowledgment format received. Got: {payload}")
    except Exception as e:
        logging.error(f"Error decoding acknowledgment: {e}")

""" Send the latest firmware file to a specified client.
    This function handles the process of transferring a firmware update file to a client 
    over a specified topic. The file is read in chunks and sent sequentially to ensure 
    compatibility with network constraints."""
def send_firmware_update(client_ip):
    try:
        logging.info(f"Sending the latest firmware file to Client {client_ip}...")
        with open(latest_file_path, "rb") as file:
            chunk_size = 1024  # Adjust based on your file size
            topic = topic_file_transfer.format(client_ip=client_ip)

            # Send the file in chunks
            while chunk := file.read(chunk_size):
                client.publish(topic, chunk)
                logging.info(f"Sent a chunk to Client {client_ip}.")
        
        logging.info(f"Firmware file sent successfully to Client {client_ip}.")
        return True
    except FileNotFoundError:
        logging.error(f"Error: Firmware file not found at {latest_file_path}")
    except Exception as e:
        logging.error(f"Error sending firmware file to {client_ip}: {e}")
    return False

""" Callback function triggered when the MQTT client connects to the broker.
    This function is invoked automatically by the MQTT client when a connection 
    with the broker is established. It handles subscription to necessary topics 
    based on the connection result code."""
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        #connection successful
        print("Connected to broker!")
        # Subscribe to topics
        client.subscribe(topic_device_version)  # Subscribe to version info topic
        client.subscribe(topic_device_ack)  # Subscribe to acknowledgment topics for all clients
        logging.info(f"Subscribed to topic: {topic_device_version}, {topic_device_ack}")
    elif rc == 1:
        # The broker does not support the MQTT version requested by the client.
        logging.error("Failed to connect to broker. Return code: 1 (Unacceptable protocol version)")
    elif rc == 2:
        # The client identifier is rejected by the broker (e.g., invalid or already in use).
        logging.error("Failed to connect to broker. Return code: 2 (Identifier rejected)")
    elif rc == 3:
        # The broker is unavailable or unreachable.
        logging.error("Failed to connect to broker. Return code: 3 (Server unavailable)")
    elif rc == 4:
        # The username or password provided by the client is incorrect.
        logging.error("Failed to connect to broker. Return code: 4 (Bad username or password)")
    elif rc == 5:
        # The client is not authorized to connect to the broker.
        logging.error("Failed to connect to broker. Return code: 5 (Not authorized)")
    else:
        # Any other return code indicates an unknown or unexpected error.
        logging.error(f"Failed to connect to broker. Return code: {rc} (Unknown error)")

""" Callback function triggered when the MQTT server receives a message.
    This function handles incoming messages from subscribed topics. Depending on the topic, 
    it processes device version updates or acknowledgment messages from clients."""
def on_message(client, userdata, msg):
    global selected_clients

    if msg.topic.startswith(topic_device_version):
        payload = msg.payload.decode("utf-8")
        try:
            client_id, received_version = payload.split(":")
            client_id = client_id.replace('IP Address: ', '').strip()
            received_version = received_version.replace('Version: ', '').strip()
            logging.info(f"Received version from client {client_id}: {received_version}")

            # Validate client
            if not validate_client(client_id):
                logging.info(f"Client {client_id} is not in the selected clients list")
                return
            
            # Store the received device details in JSON format
            device_details = {client_id: received_version}
            save_device_details(device_details)
            
            # Compare versions
            version_status = compare_versions(client_id, received_version, Server_Version)
            
            if version_status == "outdated":
                if send_firmware_update(client_id):
                    logging.info(f"Update sent successfully to Client {client_id}. Waiting for acknowledgment...")
                    with selected_clients_lock:
                        acknowledgment_pending.add(client_id)  # Add client to acknowledgment tracking
                else:
                    logging.warning(f"Failed to update Client {client_id}. Will retry later.")
        except ValueError:
            logging.error(f"Error: Received malformed version payload: {payload}")
    elif msg.topic.startswith("File/Ack/"):
        client_id = msg.topic.split("/")[-1]
        if validate_client(client_id):
            payload = msg.payload.decode("utf-8")
            process_acknowledgment(payload)

# MQTT Setup
broker = "192.168.20.53"  # Change to the actual broker address
mqtt_topic = os.getenv("MQTT_TOPIC")
load_selected_clients()
#selected_clients = set(os.getenv("SELECTED_CLIENTS", "").split(","))
#print(f"Publisher side selected clients: {selected_clients}")

#`SELECTED_CLIENTS` specifies the list of clients that the server is configured to handle.
if not selected_clients:
    logging.error("Error: SELECTED_CLIENTS environment variable is not set or empty. Exiting...")
    exit(1)

#`MQTT_TOPIC` defines the topic used for communication with the MQTT broker.
if not mqtt_topic:
    logging.error("Error: MQTT_TOPIC environment variable is not set. Exiting...")
    exit(1)

# MQTT Client
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

# Connect to the broker
logging.info("Connecting to broker...")
client.connect(broker, 1883, 60)

# Start the MQTT loop
client.loop_forever()
