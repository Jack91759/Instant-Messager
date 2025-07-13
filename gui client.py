import datetime
import socket
import threading
import tkinter as tk
from tkinter import simpledialog, messagebox, scrolledtext
import time

# Client V2 Configuration
HOST = '127.0.0.1'
PORT = 65432


class ChatClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect_to_server()

        self.role = 'user'  # Default role

        # Main Chat Window
        self.root = tk.Tk()
        self.root.title("Chat")
        self.root.geometry("400x420")  # Adjusted height to accommodate the message bar

        self.text_area = scrolledtext.ScrolledText(self.root, state='disabled')
        self.text_area.pack(expand=True, fill=tk.BOTH)
        self.text_area.tag_config('admin', foreground='red')  # Configure the admin tag color
        self.text_area.tag_config('user', foreground='black')  # Default user color

        self.msg_label = tk.Label(self.root, text="Message:")
        self.msg_label.pack(side=tk.LEFT, padx=5, pady=5)

        self.input_area = tk.Text(self.root, height=3)
        self.input_area.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.BOTH, expand=True)

        self.send_button = tk.Button(self.root, text="Send", command=self.write)
        self.send_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.root.bind('<Return>', lambda event: self.write())

        # Online Users Window
        self.online_users_window = tk.Toplevel(self.root)
        self.online_users_window.title("Online Users")
        self.online_users_window.geometry("200x300")

        self.online_users_label = tk.Label(self.online_users_window, text="Online Users:")
        self.online_users_label.pack(padx=5, pady=5)

        self.users_list = tk.Listbox(self.online_users_window)
        self.users_list.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)

        # Friends Window
        # self.friends_window = tk.Toplevel(self.root)
        # self.friends_window.title("Friends")
        # self.friends_window.geometry("200x300")

        # self.friends_label = tk.Label(self.friends_window, text="Friends:")
        # self.friends_label.pack(padx=5, pady=5)

        # self.friends_list = tk.Listbox(self.friends_window)
        # self.friends_list.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)

        # Username and Authentication
        self.username = simpledialog.askstring("Login/Register",
                                               "Please enter your username or type 'register' to create a new account",
                                               parent=self.root)
        if self.username.lower() == 'register':
            self.register()
        else:
            self.password = simpledialog.askstring("Login", "Please enter your password", parent=self.root)
            self.client_socket.send(f"{self.username}".encode('utf-8'))
            self.client_socket.send(f"{self.password}".encode('utf-8'))

            self.receive_thread = threading.Thread(target=self.receive)
            self.receive_thread.start()

            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.root.mainloop()

    def connect_to_server(self):
        while True:
            try:
                self.client_socket.connect((self.host, self.port))
                break
            except socket.error:
                print("[INFO] Server unavailable, retrying in 5 seconds...")
                time.sleep(5)

    def write(self):
        msg = self.input_area.get("1.0", 'end-1c')
        self.log_message(f"[{self.username}] {msg}")  # Log message locally
        self.client_socket.send(msg.encode('utf-8'))
        self.input_area.delete('1.0', 'end')
        # Display the sent message in the chat window
        self.display_message(f"[{self.username}] {msg}", 'admin' if self.role == 'admin' else 'user')

    def receive(self):
        while True:
            try:
                msg = self.client_socket.recv(1024).decode('utf-8')
                if not msg:
                    raise ConnectionError
                if 'USERNAME' in msg:
                    self.display_message(f"[SERVER] Successfully logged in", 'admin' if self.role == 'admin' else 'user')
                elif 'PASSWORD' in msg:
                    print('test')
                elif "ONLINE USERS:" in msg:
                    users = msg.split("ONLINE USERS: ")[1]
                    self.update_users_list(users)
                elif msg.startswith("ROLE"):
                    self.role = msg.split(": ")[1]
                else:
                    self.display_message(msg, 'admin' if '[Admin]' in msg else 'user')
            except (ConnectionError, OSError):
                print("[ERROR] Connection lost. Attempting to reconnect...")
                self.client_socket.close()
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.connect_to_server()
                self.client_socket.send(f"{self.username}".encode('utf-8'))
                time.sleep(3)
                self.client_socket.send(f"{self.password}".encode('utf-8'))

    def update_users_list(self, users):
        self.users_list.delete(0, 'end')

        red_users = []
        yellow_users = []
        normal_users = []

        for user in users.split(", "):
            if '\033[91m' in user:
                red_users.append(user.replace('\033[91m', '').replace('\033[0m', ''))
            elif '\033[93m' in user:
                yellow_users.append(user.replace('\033[93m', '').replace('\033[0m', ''))
            else:
                normal_users.append(user)

        # Insert red users first and color them red
        for user in red_users:
            self.users_list.insert('end', user)
            self.users_list.itemconfig('end', {'fg': 'red'})

        # Then yellow users (default color)
        for user in yellow_users:
            self.users_list.insert('end', user)

        # Then normal users
        for user in normal_users:
            self.users_list.insert('end', user)

    def register(self):
        new_username = simpledialog.askstring("Registration", "Please choose a new username", parent=self.root)
        new_password = simpledialog.askstring("Registration", "Please choose a password", parent=self.root)
        role = 'user'
        self.client_socket.send("REGISTER".encode('utf-8'))
        self.client_socket.send(new_username.encode('utf-8'))
        self.client_socket.send(new_password.encode('utf-8'))
        self.client_socket.send(role.encode('utf-8'))
        response = self.client_socket.recv(1024).decode('utf-8')
        if response == "REGISTERED":
            messagebox.showinfo("Registration", "Registration successful. Please login with your new account.")
            self.username = simpledialog.askstring("Login", "Please enter your username", parent=self.root)
            self.password = simpledialog.askstring("Login", "Please enter your password", parent=self.root)
            self.client_socket.send(f"{self.username}\n{self.password}".encode('utf-8'))

            self.receive_thread = threading.Thread(target=self.receive)
            self.receive_thread.start()

            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.root.mainloop()
        else:
            messagebox.showerror("Registration", "Registration failed. Username may already be taken.")
            self.root.destroy()

    def log_message(self, msg):
        with open(f"{self.username}_log.txt", 'a') as f:
            f.write(f"{datetime.datetime.now()}: {msg}\n")

    def on_closing(self):
        self.client_socket.close()
        self.root.destroy()

    def display_message(self, msg, tag='user'):
        self.text_area.config(state='normal')
        self.text_area.insert('end', msg + '\n', tag)
        self.text_area.yview('end')
        self.text_area.config(state='disabled')


if __name__ == "__main__":
    client = ChatClient(HOST, PORT)
