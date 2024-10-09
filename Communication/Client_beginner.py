import os
import subprocess
import time
import socket
import logging

# Set the folder path where the log file should be stored
log_folder = r'/Users/Yi-An/Documents/000_Project/044_FAARM_PA-004/Data/Logfile'  # You can specify an absolute path as well, like '/var/log/myapp/'
log_file = 'Communication.log'

# Ensure the folder exists
if not os.path.exists(log_folder):
    os.makedirs(log_folder)  # Create the folder if it doesn't exist

#%%
# Set up logging with the file path (folder + file name)
log_path = os.path.join(log_folder, log_file)
logging.basicConfig(
    filename=log_path,  # Log file path
    level=logging.INFO,  # Log level
    format='%(asctime)s - %(levelname)s - %(message)s'  # Log format
)

logging.info("This is the test log entry from client.")



#%% Create a client, Send message and close the connection
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('localhost', 8080))
logging.info("Client connected to server")
time.sleep(1)
# Send a request to the server
message = "Hello, Server! This is Client 1"
client_socket.send(message.encode('utf-8'))
logging.info(f"Request sent: {message}")
time.sleep(1)
# Receive the response from the server
response = client_socket.recv(1024).decode('utf-8')
logging.info(f"Response received from server: {response}")
time.sleep(1)
# Close the connection
client_socket.close()
logging.info("Client connection closed")

#%% Create a client2, Send message and close the connection
client_socket2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket2.connect(('localhost', 8080))
logging.info("Client2 connected to server")
time.sleep(1)
# Send a request to the server
message = "Hello, Server! This is Client 2, PLEASE PRINT 'Taiwan NO.1' FOR 3 TIMES"
client_socket2.send(message.encode('utf-8'))
logging.info(f"Request sent: {message}")
time.sleep(1)
#%% Receive the response from the server
response = client_socket2.recv(1024).decode('utf-8')
logging.info(f"Response received from server: {response}")
time.sleep(1)
# Close the connection
client_socket2.close()
logging.info("Client2 connection closed")

