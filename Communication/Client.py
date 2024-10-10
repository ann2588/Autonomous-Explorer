import os
import subprocess
import time
import socket

# Assume the print() will be overwrite by logging.info

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
    global client_socket
    try:
        # Initialize or reconnect if the socket is closed or uninitialized
        if client_socket is None or not is_socket_open(client_socket):
            initialize_socket()
            client_socket.connect(('localhost', 8080))
            print("Client connected to server")
            time.sleep(1)

        # Send a request to the server
        client_socket.send(COMMAND.encode('utf-8'))
        logging.info(f"Request sent: {COMMAND}")
        time.sleep(1)
    except Exception as e:
        print(f"Error while sending command: {e}")
        client_socket = None  # Mark socket as closed

def CheckSignalFromServer():
    global client_socket, logging
    try:
        if client_socket is None or not is_socket_open(client_socket):
            print("Socket is closed or unavailable.")
            return False

        # Set a timeout for the response
        client_socket.settimeout(1.0)

        # Attempt to receive the response from the server
        response = client_socket.recv(1024).decode('utf-8')
        print(f"Response from server: {response}")
        return True  # Successfully received response
    except socket.timeout:
        print("No response from server within 1 second")
        return False  # Timed out without a response
    except Exception as e:
        print(f"Error while receiving signal: {e}")
        return False  # Some error occurred
    finally:
        # Close the connection after receiving the message
        if client_socket:
            client_socket.close()
            print("Client connection closed")
            client_socket = None  # Mark socket as closed


def SendCommandToGC(COMMAND):
    global client_socket
    try:
        # Initialize or reconnect if the socket is closed or uninitialized
        if client_socket is None or not is_socket_open(client_socket):
            initialize_socket()
            client_socket.connect(('localhost', 8080))
            print("Client connected to server")
            time.sleep(1)

        # Send a request to the server
        client_socket.send(COMMAND.encode('utf-8'))
        print(f"Request sent: {COMMAND}")
        time.sleep(1)
    except Exception as e:
        print(f"Error while sending command: {e}")
        client_socket = None  # Mark socket as closed

def CheckSignalFromGC():
    global client_socket, logging
    try:
        if client_socket is None or not is_socket_open(client_socket):
            print("Socket is closed or unavailable.")
            return False

        # Set a timeout for the response
        client_socket.settimeout(1.0)

        # Attempt to receive the response from the server
        response = client_socket.recv(1024).decode('utf-8')
        print(f"Response from server: {response}")
        return True  # Successfully received response
    except socket.timeout:
        print("No response from server within 1 second")
        return False  # Timed out without a response
    except Exception as e:
        print(f"Error while receiving signal: {e}")
        return False  # Some error occurred
    finally:
        # Close the connection after receiving the message
        if client_socket:
            client_socket.close()
            print("Client connection closed")
            client_socket = None  # Mark socket as closed