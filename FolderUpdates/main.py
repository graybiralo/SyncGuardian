from tkinter import Tk, Label, Button, Text, Scrollbar, VERTICAL, END, DISABLED, NORMAL 
from tkinter.simpledialog import askstring
from folder_selector import FolderSelector
import socket
import time
import threading
import json

class FolderManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SyncGuardian")

        # Initialize folder selector with status and log callbacks
        self.folder_selector = FolderSelector(self.update_status, self.log_message)

        # Title
        Label(root, text="Track Changes in Real Time", font=("Helvetica", 16)).pack(pady=10)

        # Buttons
        self.select_folder_button = Button(root, text="Select Folder", command=self.folder_selector.open_folder_dialog, width=20)
        self.select_folder_button.pack(pady=5)

        self.start_server_button = Button(root, text="Start Server", command=self.start_server, width=20)
        self.start_server_button.pack(pady=5)

        self.stop_server_button = Button(root, text="Stop Server", command=self.stop_server, width=20, state="disabled")
        self.stop_server_button.pack(pady=5)

        self.connect_client_button = Button(root, text="Connect to Server", command=self.connect_client, width=20)
        self.connect_client_button.pack(pady=5)

        self.disconnect_server_button = Button(root, text="Disconnect from Server", command=self.disconnect_server, width=20, state="disabled")
        self.disconnect_server_button.pack(pady=5)

        self.start_monitoring_button = Button(root, text="Start Monitoring", command=self.start_monitoring, width=20, state="disabled")
        self.start_monitoring_button.pack(pady=5)

        self.stop_monitoring_button = Button(root, text="Stop Monitoring", command=self.stop_monitoring, width=20, state="disabled")
        self.stop_monitoring_button.pack(pady=5)

        self.exit_button = Button(root, text="Exit", command=self.exit_app, width=20)
        self.exit_button.pack(pady=5)

        # Monitoring Status Label
        self.status_label = Label(root, text="Monitoring Status: Inactive", font=("Helvetica", 12))
        self.status_label.pack(pady=10)

        # Log Display
        self.log_text = Text(root, height=15, wrap="word", state=DISABLED)
        self.log_text.pack(padx=10, pady=10, fill="both", expand=True)

        # Scrollbar
        self.scrollbar = Scrollbar(root, orient=VERTICAL, command=self.log_text.yview)
        self.scrollbar.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=self.scrollbar.set)

        # Close handling for the root window
        self.root.protocol("WM_DELETE_WINDOW", self.exit_app)

        # Client socket for disconnecting
        self.client_socket = None

    #update monitoring status
    def update_status(self, message):
        self.status_label.config(text=f"Monitoring Status: {message}")
        if message == "Active":
            self.start_monitoring_button.config(state="disabled")
            self.stop_monitoring_button.config(state="normal")
        elif message == "Inactive":
            self.start_monitoring_button.config(state="normal")
            self.stop_monitoring_button.config(state="disabled")

    #log messages
    def log_message(self, message):
        self.log_text.config(state=NORMAL)
        self.log_text.insert(END, message + "\n")
        self.log_text.config(state=DISABLED)
        self.log_text.see(END)


    #starting server
    def start_server(self):
        try:
            # Start the server on localhost and port 5000
            threading.Thread(target=self.folder_selector.start_server, args=("0.0.0.0", 5000), daemon=True).start()
            self.stop_server_button.config(state="normal")
            self.connect_client_button.config(state="disabled")
            self.start_server_button.config(state="disabled")
        except Exception as e:
            self.log_message(f"Error starting server: {e}")

    #stopping the server
    def stop_server(self):
        try:
            self.folder_selector.stop_server()
            
            # Ensure buttons are reset to the proper states
            self.stop_server_button.config(state="disabled")
            self.start_server_button.config(state="normal")
            self.connect_client_button.config(state="normal")
            self.disconnect_server_button.config(state="disabled")
            
            # ensure the client socket is cleared and buttons are reset
            if self.client_socket:
                self.client_socket.close()
                self.client_socket = None
            
        except Exception as e:
            self.log_message(f"Error stopping server: {e}")


    #connecting the clients
    def connect_client(self):
        try:
            server_ip = askstring("Server IP", "Enter Server IP:")
            server_port = askstring("Server Port", "Enter Server Port:")
            if server_ip and server_port:
                threading.Thread(target=self.start_client, args=(server_ip, int(server_port)), daemon=True).start()

                self.connect_client_button.config(state="disabled")
        except Exception as e:
            self.log_message(f"Error connecting client: {e}")
            self.connect_client_button.config(state="normal")


    #clients start connecting
    def start_client(self, server_ip, server_port):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client_socket.connect((server_ip, server_port))
            self.log_message("Connected to server.")

            self.connect_client_button.config(state="disabled")
            self.disconnect_server_button.config(state="normal")
            self.start_server_button.config(state="disabled")
            self.stop_server_button.config(state="disabled")

            while self.client_socket:
                try:
                    data = self.client_socket.recv(1024)
                    if not data:
                        self.log_message("Server has disconnected.")
                        break

                    # Safely parse the received JSON data
                    try:
                        message = json.loads(data.decode("utf-8"))
                        message_type = message.get("type", "Unknown")
                        path = message.get("path", "Unknown")

                        if message_type == "server_stopped":
                            self.log_message(f"Server stopped: {path}")
                            
                            # Reset buttons when server is stopped
                            self.start_server_button.config(state="normal")
                            self.connect_client_button.config(state="normal")
                            self.disconnect_server_button.config(state="disabled")
                            break
                        
                        self.log_message(f"{message_type.replace('_', ' ').title()}: {path}")
                    except json.JSONDecodeError as e:
                        self.log_message(f"Error decoding JSON: {e}")
                        break

                except (ConnectionResetError, BrokenPipeError):
                    self.log_message("Connection lost: Server has stopped.")
                    break
                except Exception as e:
                    if self.client_socket:
                        self.log_message(f"Error receiving data: {e}")
                    break
        except ConnectionRefusedError:
            self.log_message("Error connecting to server: Connection refused. Ensure the server is running.")
            self.connect_client_button.config(state="normal")
        except Exception as e:
            self.log_message(f"Error connecting to server: {e}")
            self.connect_client_button.config(state="normal")
        finally:
            if self.client_socket:
                self.client_socket.close()
            self.client_socket = None
            self.connect_client_button.config(state="normal")
            self.disconnect_server_button.config(state="disabled")

            
    def reset_buttons_after_server_stop(self):
        self.connect_client_button.config(state="normal")
        self.start_server_button.config(state="normal")
        self.stop_server_button.config(state="disabled")
        self.disconnect_server_button.config(state="disabled")

    #disconnection from the server
    def disconnect_server(self):
        try:
            if self.client_socket:
                # Send a disconnect message to the server
                disconnection_message = json.dumps({"type": "disconnect"}).encode("utf-8")
                self.client_socket.sendall(disconnection_message)

                # Close the client socket
                self.client_socket.close()
                self.client_socket = None

                self.start_server_button.config(state="normal")
                self.connect_client_button.config(state="normal")
                self.disconnect_server_button.config(state="disabled")
        except Exception as e:
            self.log_message(f"Error disconnecting from server: {e}")


    #monitoring start
    def start_monitoring(self):
        self.folder_selector.start_monitoring()

    #monitoring stop
    def stop_monitoring(self):
        self.folder_selector.stop_monitoring()

    
    #exiting    
    def exit_app(self):
        self.folder_selector.stop_monitoring()
        self.root.destroy()


if __name__ == "__main__":
    root = Tk()
    app = FolderManagerApp(root)
    root.mainloop()
