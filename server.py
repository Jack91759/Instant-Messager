import socket
import threading
import datetime
import os
import json
import sqlite3

# Server Configuration
HOST = '127.0.0.1'
PORT = 65432

# Database Configuration
DB_FILE = 'user_profiles.db'


# Create SQLite database table for user profiles
def create_user_table():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'user'
                )''')
    conn.commit()
    conn.close()


# Insert new user into the database
def insert_user(username, password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


# Dictionary to store client connections and their usernames
clients = {}

# Dictionary to store authenticated users and their connections
authenticated_users = {}

# Dictionary to store roles of users (admin/user)
roles = {}

# Dictionary to store friends list of each user
friends = {}

# Dictionary to store user colors
user_colors = {}

# File to store chat log
chat_log_file = 'chat_log.json'

# ANSI color codes
color_codes = {
    '0;30': 'black',
    'red': '0;31',
    'green': '0;32',
    'yellow': '0;33',
    'blue': '0;34',
    'magenta': '0;35',
    'cyan': '0;36',
    'white': '0;37'
}

# Handle Client Connections
def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    conn.send("USERNAME\n".encode('utf-8'))

    username = conn.recv(1024).decode('utf-8').strip()
    conn.send("PASSWORD\n".encode('utf-8'))
    password = conn.recv(1024).decode('utf-8').strip()

    if authenticate_user(username, password):
        print(f"[AUTHENTICATED] {username} has joined.")
        clients[conn] = username
        authenticated_users[username] = conn
        broadcast(f"{username} has joined the chat!", conn)
        update_online_users()
        handle_messages(conn, username)
    elif username == "REGISTER":
        register_user(conn)
    else:
        print(f"[UNAUTHORIZED] {username} failed to authenticate.")
        conn.send("UNAUTHORIZED\n".encode('utf-8'))
        conn.close()


# Authenticate User
def authenticate_user(username, password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = c.fetchone()
    conn.close()
    if user:
        roles[username] = user[3]  # Store user role
        friends[username] = set()  # Initialize an empty friends list
        user_colors[username] = 'black'  # Default color for new users
        return True
    return False


# Register new user
def register_user(conn):
    print("Register")
    conn.send("NEW_USERNAME\n".encode('utf-8'))
    new_username = conn.recv(1024).decode('utf-8').strip()
    print(new_username)
    conn.send("NEW_PASSWORD\n".encode('utf-8'))
    new_password = conn.recv(1024).decode('utf-8').strip()
    print(new_password)
    if insert_user(new_username, new_password):
        conn.send("REGISTERED\n".encode('utf-8'))
    else:
        conn.send("REGISTRATION_FAILED\n".encode('utf-8'))


# Handle Incoming Messages
def handle_messages(conn, username):
    connected = True
    while connected:
        try:
            msg = conn.recv(1024).decode('utf-8')
            if msg:
                if msg.startswith("/addfriend"):
                    handle_add_friend(conn, username, msg)
                elif msg.startswith("/removefriend"):
                    handle_remove_friend(conn, username, msg)
                elif msg.startswith("/disconnect"):
                    handle_disconnect(conn, username, msg)
                elif msg.startswith("/color"):
                    handle_color_change(conn, username, msg)
                else:
                    log_message = f"[{username}] {msg}"
                    print(log_message)
                    save_chat_log(log_message)
                    broadcast(log_message, conn)
            else:
                connected = False
        except:
            connected = False

    if conn in clients:
        del clients[conn]
    if username in authenticated_users:
        del authenticated_users[username]

    conn.close()
    print(f"[DISCONNECTED] {username} disconnected.")
    broadcast(f"{username} has left the chat.", conn)
    update_online_users()


# Handle Color Change Request
def handle_color_change(conn, username, msg):
    if roles[username] == 'admin':
        try:
            _, target_username, color = msg.split()
            if target_username in authenticated_users and color in color_codes:
                user_colors[target_username] = color_codes[color]
                conn.send(f"Changed {target_username}'s color to {color}.\n".encode('utf-8'))
                broadcast(f"{target_username}'s color has been changed to {color} by an admin.\n", conn)
            else:
                conn.send("Invalid username or color.\n".encode('utf-8'))
        except ValueError:
            conn.send("Invalid command format. Use /color <username> <color>.\n".encode('utf-8'))
    else:
        conn.send("You do not have permission to use this command.\n".encode('utf-8'))


# Broadcast Message to All Clients
def broadcast(msg, connection=None):
    for client in list(clients):  # Use list to create a copy of keys
        if client != connection:
            try:
                print(msg)
                client.send(msg.encode('utf-8'))
            except Exception as e:
                print(f"[ERROR] Failed to send message to {clients[client]}: {e}")
                client.close()
                del clients[client]


# Send Updated List of Online Users
def update_online_users():
    users_list = []
    for conn, username in clients.items():
        role = roles.get(username, 'user')
        color_code = user_colors.get(username, '0;30')  # Default to black if not set
        if role == 'admin':
            users_list.append(f"\033[91m{username} (admin)\033[0m")  # Red color for admin
        else:
            color_code = "93"
            users_list.append(f"\033[{color_code}m{username}\033[0m")  # Use the stored color for user
    users = "ONLINE USERS: " + ", ".join(users_list)
    for client in clients:
        try:
            client.send(users.encode('utf-8'))
        except:
            client.close()
            del clients[client]


# Save Chat Log to JSON File
def save_chat_log(message):
    with open(chat_log_file, 'a') as f:
        json.dump({"timestamp": str(datetime.datetime.now()), "message": message}, f)
        f.write('\n')


# Send Chat History to New Client V1
def send_chat_history(conn):
    if os.path.exists(chat_log_file):
        with open(chat_log_file, 'r') as f:
            for line in f:
                conn.send(line.encode('utf-8'))


# Handle Add Friend Request
def handle_add_friend(conn, username, msg):
    friend_username = msg.split()[1]
    if friend_username in authenticated_users:
        # Your implementation for adding a friend
        pass
    else:
        conn.send(f"User {friend_username} not found.\n".encode('utf-8'))


# Handle Remove Friend Request
def handle_remove_friend(conn, username, msg):
    friend_username = msg.split()[1]
    if friend_username in friends[username]:
        # Your implementation for removing a friend
        pass
    else:
        conn.send(f"User {friend_username} not in friends list.\n".encode('utf-8'))


# Handle Disconnect Command
def handle_disconnect(conn, username, msg):
    if roles[username] == 'admin':
        target_username = msg.split()[1]
        if target_username in authenticated_users:
            target_conn = authenticated_users[target_username]
            target_conn.close()
            del clients[target_conn]
            del authenticated_users[target_username]
            broadcast(f"{target_username} has been disconnected by an admin.\n", conn)
            update_online_users()
        else:
            conn.send(f"User {target_username} not found.\n".encode('utf-8'))
    else:
        conn.send("You do not have permission to use this command.\n".encode('utf-8'))


# Main Function
def start():
    if not os.path.exists(chat_log_file):
        open(chat_log_file, 'w').close()

    create_user_table()

    server.listen()
    print(f"[LISTENING] Server is listening on {HOST}:{PORT}")
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")


# Initialize Server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))

print("[STARTING] Server is starting...")
start()
