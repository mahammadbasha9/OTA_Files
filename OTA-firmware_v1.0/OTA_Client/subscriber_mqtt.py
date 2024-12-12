import os
import paho.mqtt.client as mqtt
import socket  # To get the device's real-time IP address

# Client Configuration
client_version = "1.0"  # Client's firmware version
client_ip = ""  # Will hold the device's real-time IP address
topic_version = "metadata/version"  # Topic to send version info to the server
topic_transfer = "File/Transfer/{client_ip}"  # Topic for receiving firmware updates
received_file_path = "received_firmware.bin"  # Path to save the received firmware file

# This function is called when the client connects to the broker
def on_connect(client, userdata, flags, rc):
    print("Connected to broker!")

    # Subscribe to the transfer topic for this client
    client_ip = userdata["client_ip"]
    transfer_topic = topic_transfer.format(client_ip=client_ip)
    client.subscribe(transfer_topic)
    print(f"Subscribed to topic: {transfer_topic}")

    # Send the client version to the server to check for updates
    client.publish(topic_version, f"{client_ip}:{client_version}")
    print(f"Sent client version: {client_version} with Client IP: {client_ip}")

# This function is called when the client receives a message from the broker
def on_message(client, userdata, msg):
    # Receive firmware chunks and save them to a file
    try:
        with open(received_file_path, "ab") as file:  # 'ab' mode to append binary data
            file.write(msg.payload)
            print("Received a chunk of firmware.")
    except Exception as e:
        print(f"Error receiving firmware chunk: {e}")
    finally:
        # Check if the transfer is complete
        file_size = os.path.getsize(received_file_path)
        send_acknowledgment(client, userdata["client_ip"], file_size)

# Function to get the real-time device IP address
def get_device_ip():
    try:
        hostname = socket.gethostname()
        device_ip = socket.gethostbyname(hostname)
        return device_ip
    except Exception as e:
        print(f"Error retrieving device IP address: {e}")
        return "Unknown IP"

# Function to send acknowledgment to the server(publisher)
def send_acknowledgment(client, ip_address, file_size):
    try:
        ack_message = f"IP Address: {ip_address}, File Size: {file_size} bytes"  # New format
        client.publish(f"File/Ack/{client_ip}", ack_message)
        print(f"Sent acknowledgment: {ack_message}")
    except Exception as e:
        print(f"Error sending acknowledgment: {e}")

# Set up the MQTT client
def setup_mqtt_client(client_id, client_ip):
    client = mqtt.Client(client_id)
    client.user_data_set({'client_id': client_id, 'client_ip': client_ip})
    client.on_connect = on_connect
    client.on_message = on_message
    return client

# MQTT Setup
client_ip = get_device_ip() 
client_id = client_ip
broker = "192.168.20.53"  # Change to the IP address of the broker if not localhost
client = setup_mqtt_client(client_id, client_ip)

# Connect to the broker
print("Connecting to broker...")
client.connect(broker, 1883, 60)

# Start the MQTT loop to handle incoming messages and maintain the connection
client.loop_forever()
