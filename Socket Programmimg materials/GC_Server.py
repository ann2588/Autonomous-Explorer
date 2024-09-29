#%% Treat GC as server for communication to do subprocessing
import socket

#%% Create a socket object
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#%% Bind to localhost and a port
server_socket.bind(('localhost', 12345))

#%% Put the socket into listening mode
server_socket.listen(1)
print("Server is listening...")

#%% Accept a client connection
client_socket, client_address = server_socket.accept()
print(f"Connection from: {client_address}")

#%% Receive data from the client
data = client_socket.recv(1024).decode()
print(f"Received from client: {data}")

#%% Send a response to the client
client_socket.send(b"Hello from the server!")

#%% Close the client connection
client_socket.close()
server_socket.close()

#%%
import socket
import threading

#%%
# Function to handle a client connection
def handle_client(client_socket, client_address):
    print(f"New connection from {client_address}")

    # Receive and respond to client messages
    while True:
        try:
            # Receive data from the client
            data = client_socket.recv(1024)
            if not data:
                # No more data; client has disconnected
                print(f"Connection closed by {client_address}")
                break

            print(f"Received from {client_address}: {data.decode()}")

            # Send a response back to the client
            client_socket.send(b"Message received")
        except:
            print(f"Error handling the client {client_address}")
            break

    # Close the client connection
    client_socket.close()

# Set up the server
def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 12345))
    server_socket.listen(5)
    print("Server is listening...")

    while True:
        # Accept a client connection
        client_socket, client_address = server_socket.accept()

        # Create a new thread to handle the client
        client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
        client_thread.start()

# Start the server
if __name__ == "__main__":
    start_server()