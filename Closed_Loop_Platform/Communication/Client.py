import os
import subprocess
import time
import socket

# Global variable for the client socket
client_socket = None
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

        # Set a timeout for receiving the response (in seconds)
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
        return False  # Some other error occurred

    finally:
        # Close the socket only if it was supposed to close (e.g., based on a condition)
        if should_close_socket(response) == True:
            client_socket.close()
            print("Client connection closed.")
            client_socket = None  # Mark socket as closed
        else:
            print("Client connection stayed opened.")



def should_close_socket(RESPONSE):
    """Define the logic to determine whether the socket should be closed."""
    close_or_not = True if RESPONSE != None else False
    return close_or_not  # Example: Keep the socket open


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
    response = None  # Initialize response to avoid UnboundLocalError
    try:
        # Check if the socket is available and open
        if client_socket is None or not is_socket_open(client_socket):
            print("Socket is closed or unavailable.")
            return False

        # Set a timeout for receiving the response (in seconds)
        client_socket.settimeout(30)

        # Attempt to receive the response from the server
        response = client_socket.recv(1024).decode('utf-8')
        print(f"Response from server: {response}")
        return True, response  # Successfully received response

    except socket.timeout:
        print("No response from server within 30 second.")
        return False  # Timed out without a response

    except Exception as e:
        print(f"Error while receiving signal: {e}")
        return False  # Some other error occurred

    finally:
        # Close the socket only if required by specific logic
        if should_close_socket(response):
            client_socket.close()
            print("Client connection closed.")
            client_socket = None  # Mark socket as closed
        else:
            print("Client connection stayed open.")

def is_socket_open(sock):
    """Helper function to check if a socket is open and operational."""
    try:
        # Try sending an empty byte string to check the socket status
        sock.send(b"")
        return True
    except socket.error:
        return False

def should_close_socket(response):
    """Define the logic to determine whether the socket should close."""
    # Example: Close the socket only if the server sends a specific keyword
    if response:
        return True
    return False
