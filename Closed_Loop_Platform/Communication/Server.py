import os, sys
import socket
import logging
import time
import subprocess

# Get the absolute path of the parent directory of Closed_Loop_Platform
closed_loop_path = os.path.abspath(R"C:\Users\guazh\PycharmProjects\CO2Platform")

# Add the parent directory to the Python path
sys.path.append(closed_loop_path)

print(f"Added to Python path: {closed_loop_path}")

from Closed_Loop_Platform.Communication.gasanalyzer import *



def kill_port(port):
    try:
        # Find the PID of the process using the port
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True,
            text=True,
            check=True
        )
        # Filter lines containing the port
        lines = result.stdout.splitlines()
        for line in lines:
            if f":{port}" in line:
                parts = line.split()
                pid = parts[-1]  # The last column is the PID
                # Kill the process with the found PID
                subprocess.run(["taskkill", "/PID", pid, "/F"], check=True)
                print(f"Port {port} is now free (Process {pid} killed).")
                return
        print(f"No process is using port {port}.")
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")


# Set the folder path where the log file should be stored
log_folder = r"C:\Users\guazh\data"  # You can specify an absolute path as well, like '/var/log/myapp/'
log_file = 'server.log'

# Ensure the folder exists
if not os.path.exists(log_folder):
    os.makedirs(log_folder)  # Create the folder if it doesn't exist

# Set up logging with the file path (folder + file name)
log_path = os.path.join(log_folder, log_file)
logging.basicConfig(
    filename=log_path,  # Log file path
    level=logging.INFO,  # Log level
    format='%(asctime)s - %(levelname)s - %(message)s'  # Log format
)
logging.info("This is the first log entry from server.")  # Log file is created at this point

# Set up the Server and awaiting to receive signal
# Create server socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    server_socket.bind(('localhost', 8080))  # Bind to localhost and port 8080
except:
    kill_port(8080)
    server_socket.bind(('localhost', 8080))  # Bind to localhost and port 8080
server_socket.listen(5)  # Listen for incoming connections
print("Server is listening...")

CommandList = [
    'Connect to GC',
    'Loading Control Files',
    'Wait 180 second and start 1 sample Injections',
    'Check if still running'
    'Baking'
]
global gc
gc = GC_Connector()


# %%
while True:
    conn, addr = server_socket.accept()  # Accept a connection
    logging.info(f"Connection from {addr}")

    # Receive the message from the client
    message = conn.recv(1024).decode('utf-8')
    logging.info(f"Received message from client: {message}")

    # Process the message and take action
    if 'Connect to GC' in message:
        logging.info("GC start to connect...")
        # Simulate connecting to GC
        # reopen the peaksimple software before running this command
        main_folder = message.split('mainfolder: ')[1]
        data_path = f'C:\\Peak498Win10\\GCDATA\\{main_folder}'  # Update your folder here
        os.makedirs(data_path, exist_ok=True)
        gc.update_gc_settings(data_path)
        # Simulate connecting to GC

        time.sleep(2)
        logging.info("GC connected successfully.")
        response = "GC connected successfully."
        logging.info("GC completed connection")

    elif 'Loading Control Files' in message:
        logging.info("GC start loading control files...")
        # Simulate loading control files
        # % Load GC method and update data file saving path in GC
        ctrl_file = r"C:\Peak498Win10\GCMETHOD\Parameter\0819-2020_90-210C_11min_Onsite3.CON"  # the path of your folder
        gc.ctrl_file = ctrl_file
        gc.load_ctrl_file()  # Running error but actually successful
        subfolder = message.split('subfolder: ')[1].split(',')[0]
        filename = 'GC'+message.split('filename: ')[1]
        data_path = os.path.join(subfolder, filename)
        try:
            os.makedirs(data_path, exist_ok=True)
        except FileExistsError:
            print(f"The directory {data_path} already exists. Continuing without creating it.")
        gc.update_gc_settings(data_path, message.split('filename: ')[1])
        # Simulate loading control files

        time.sleep(2)
        logging.info("GC finished loading control files.")
        response = "GC control files loaded successfully."
        logging.info("GC completed loading control files.")

    elif 'Wait 360 second and start 1 sample Injections' in message:
        logging.info("GC waiting 450 seconds before sample injection...")
        # Simulate waiting and starting sample injection
        time.sleep(450)  # Wait for 180 seconds
        gc.set_running()
        # Simulate waiting and starting sample injection
        logging.info("GC started sample injection.")
        response = "GC started sample injection after 450 seconds."
        logging.info("GC completed sample injection.")


    elif 'still' in message:
        logging.info("Checking if GC is still running")
        # Simulate waiting and starting sample injection
        while gc.is_running():
            print('GC is still running. Wait for another minute.')
            response = ('GC is still running. Wait for another minute.')
        # Simulate waiting and starting sample injection
        logging.info("GC finished the experiment.")
        response = "GC finished the experiment."

    elif 'Running' in message:
        logging.info("Checking if GC is running")
        # Simulate waiting and starting sample injection
        while gc.is_running():
            print('GC is running.')
        # Simulate waiting and starting sample injection
        logging.info("GC is running.")
        response = "GC is running."


    elif 'Baking' in message:
        logging.info("GC loading baking control file")
        gc.ctrl_file = r"C:\Peak498Win10\GCMETHOD\Parameter\0622-2019_270C_50min_baking.CON"
        gc.load_ctrl_file()  # Running error but actually successful
        logging.info("GC start baking...")
        # Simulate baking process
        gc.set_running()
        # Simulate baking process
        time.sleep(3000)
        logging.info("GC finished baking.")
        response = "GC completed baking."
        logging.info("GC completed baking.")

    else:
        response = "Unknown command"
        logging.info("GC received unknown command")

    # Send the response to the client
    conn.send(response.encode('utf-8'))
    logging.info(f"Response sent to client: {response}")

    # Close the connection after sending the response
    conn.close()
    logging.info("Connection closed")

