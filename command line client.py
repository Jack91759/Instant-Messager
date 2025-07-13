import socket
import threading

# Client V1 Configuration
HOST = '127.0.0.1'  # The server's hostname or IP address
PORT = 65432  # The port used by the server


# Receive Messages from Server
def receive_messages(client_socket):
    while True:
        try:
            msg = client_socket.recv(1024).decode('utf-8')
            if msg:
                print(msg)
            else:
                break
        except:
            print("[ERROR] An error occurred.")
            client_socket.close()
            break


# Send Messages to Server
def send_messages(client_socket):
    while True:
        msg = input()
        client_socket.send(msg.encode('utf-8'))


# Main Function
def start():
    client_socket.connect((HOST, PORT))
    print("[CONNECTED] Connected to the server.")

    # Start Threads for Receiving and Sending Messages
    receive_thread = threading.Thread(target=receive_messages, args=(client_socket,))
    send_thread = threading.Thread(target=send_messages, args=(client_socket,))

    receive_thread.start()
    send_thread.start()


# Initialize Client V1
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
start()
