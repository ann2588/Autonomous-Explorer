import os
import subprocess
import time
import socket
from Communication.Logging import *

# Set the folder path where the log file should be stored
log_folder = r'/Users/Yi-An/Documents/000_Project/044_FAARM_PA-004/Data/Logfile'  # You can specify an absolute path as well, like '/var/log/myapp/'
log_file = 'master.log'

# Ensure the folder exists
if not os.path.exists(log_folder):
    os.makedirs(log_folder)  # Create the folder if it doesn't exist

def initialize_socket():
    global client_socket
    # Reinitialize the socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def is_socket_open(sock):
    try:
        # Attempt to send 0 bytes; if there's an issue, it will raise an exception
        sock.send(b'')
    except socket.error:
        return False
    return True

def SendCommandToServer(COMMAND):
    global client_socket, logging
    try:
        # Initialize or reconnect if the socket is closed or uninitialized
        if client_socket is None or not is_socket_open(client_socket):
            initialize_socket()
            client_socket.connect(('localhost', 8080))
            logging.info("Client connected to server")
            time.sleep(1)

        # Send a request to the server
        client_socket.send(COMMAND.encode('utf-8'))
        logging.info(f"Request sent: {COMMAND}")
        time.sleep(1)
    except Exception as e:
        logging.error(f"Error while sending command: {e}")
        client_socket = None  # Mark socket as closed

def CheckSignalFromServer():
    global client_socket, logging
    try:
        if client_socket is None or not is_socket_open(client_socket):
            logging.info("Socket is closed or unavailable.")
            return False

        # Set a timeout for the response
        client_socket.settimeout(1.0)

        # Attempt to receive the response from the server
        response = client_socket.recv(1024).decode('utf-8')
        print(f"Response from server: {response}")
        logging.info(f"Response received from server: {response}")
        return True  # Successfully received response
    except socket.timeout:
        print("No response from server within 1 second")
        logging.info("No response from server within 1 second")
        return False  # Timed out without a response
    except Exception as e:
        logging.error(f"Error while receiving signal: {e}")
        return False  # Some error occurred
    finally:
        # Close the connection after receiving the message
        if client_socket:
            client_socket.close()
            logging.info("Client connection closed")
            client_socket = None  # Mark socket as closed

#%% Example usage:
#SendCommandToServer("Hello, Server! This is Client 2, PLEASE PRINT 'Taiwan NO.1' FOR 3 TIMES")

#logging.info("Client pending execution")
#time.sleep(5)

#SIGNAL = CheckSignalFromServer()

#if SIGNAL is True:
#    SendCommandToServer("Hello, Server! This is Client 2, PLEASE PRINT 'You are awesome!' FOR 3 TIMES")

#logging.info("Client pending execution")
#time.sleep(5)
#SIGNAL = CheckSignalFromServer()