import os
import socket
import logging
import time

import os
import subprocess


def kill_port(port):
    # Find the PID of the process using the port
    result = subprocess.run(["lsof", "-t", f"-i:{port}"], capture_output=True, text=True)
    pid = result.stdout.strip()

    if pid:
        # Kill the process using the PID
        os.system(f"kill -9 {pid}")
        print(f"Process using port {port} (PID: {pid}) has been terminated.")
    else:
        print(f"No process is using port {port}.")


# Set the folder path where the log file should be stored
log_folder = r'/Users/Yi-An/Documents/000_Project/044_FAARM_PA-004/Data/Logfile'  # You can specify an absolute path as well, like '/var/log/myapp/'
log_file = 'Communication.log'

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
#% Set up the Server and awaiting to receive signal
# Create server socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    server_socket.bind(('localhost', 8080))  # Bind to localhost and port 8080
except:
    kill_port(8080)
    server_socket.bind(('localhost', 8080))  # Bind to localhost and port 8080
server_socket.listen(5)  # Listen for incoming connections
print("Server is listening...")
#%%
while True:
    conn, addr = server_socket.accept()  # Accept a connection
    logging.info(f"Connection from {addr}")

    # Receive the message from the client
    message = conn.recv(1024).decode('utf-8')
    logging.info(f"Received message from client: {message}")

    # Process the message and take action
    if "PLEASE PRINT 'Taiwan NO.1' FOR 3 TIMES" in message:
        logging.info("Server Processing 'Taiwan NO.1' request...")
        for _ in range(3):
            time.sleep(1)
            print("Taiwan NO.1")
            logging.info("Server printing Taiwan NO.1")

        response = "I printed 'Taiwan NO.1' 3 times"
        logging.info("Server Completed 'Taiwan NO.1' task")
    elif 'You are awesome!' in message:
        logging.info("Processing 'You are awesome!' request...")
        for _ in range(3):
            time.sleep(1)
            print('You are awesome!')
            logging.info('Server printing You are awesome!')
            time.sleep(1)
        response = "I printed 'You are awesome!' 3 times"
        logging.info("Server Completed 'You are awesome!' task")
    else:
        response = "Unknown command"
        logging.info("Server Received unknown command")

    # Send the response to the client
    conn.send(response.encode('utf-8'))
    logging.info(f"Response sent to client: {response}")

    # Close the connection after sending the response
    conn.close()
    logging.info("Connection closed")