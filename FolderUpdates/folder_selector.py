import socket
import threading
import json
import os
import time
from tkinter import filedialog, messagebox
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class FolderSelector:
    def __init__(self, status_callback, log_callback):
        self.folder_path = None
        self.observer = None
        self.status_callback = status_callback
        self.log_callback = log_callback
        self.server_socket = None
        self.clients = []  # List of connected clients

    # Open a dialog to select a folder.
    def open_folder_dialog(self):
        if self.observer:  # Stop monitoring the selected folder if active
            if messagebox.askyesno("Stop Monitoring", "Monitoring is currently active. Do you want to stop it and change the folder?"):
                self.stop_monitoring()
            else:
                return
        folder_path = filedialog.askdirectory(title="Select a Folder")
        if folder_path:
            self.folder_path = folder_path
            self.log_callback(f"Selected Folder: {self.folder_path}")
            self.status_callback("Inactive")
        else:
            messagebox.showwarning("No Selection", "No folder was selected.")


    # Start monitoring the selected folder.
    def start_monitoring(self):
        if not self.folder_path:
            messagebox.showwarning("No Folder", "No folder selected for monitoring.")
            return

        if self.observer is not None:
            messagebox.showinfo("Monitoring", "Monitoring is already active.")
            return

        event_handler = FolderChangeHandler(self.log_callback, self.broadcast_to_clients)
        self.observer = Observer()
        self.observer.schedule(event_handler, self.folder_path, recursive=True)
        self.observer.start()

        folder_name = os.path.basename(self.folder_path)
        self.status_callback("Active")
        self.log_callback(f"Monitoring started for {folder_name}.")

    # Stop monitoring
    def stop_monitoring(self):
        if self.observer and self.observer.is_alive():
            self.observer.stop()
            self.observer.join()
        self.observer = None

        if self.folder_path:
            folder_name = os.path.basename(self.folder_path)
            self.log_callback(f"Monitoring stopped for {folder_name}.")
        else:
            self.log_callback("No folder was being monitored.")
        self.status_callback("Inactive")

    # Start server with SO_REUSEADDR option
  
    def start_server(self, host="0.0.0.0", port=5000):
        if hasattr(self, 'server_socket') and self.server_socket:
            self.log_callback(f"Server is already running on {host}:{port}")
            return

        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((host, port))
            self.server_socket.listen(5)

            self.server_running = True  # Flag to indicate the server is running
            self.log_callback(f"Server started on {host}:{port}")

            # Start accepting clients in a separate thread
            self.accept_thread = threading.Thread(target=self.accept_clients, daemon=True)
            self.accept_thread.start()

        except Exception as e:
            self.log_callback(f"Error starting server on {host}:{port} - {e}")


    #stoping the server
    def stop_server(self):
        if not self.server_socket:
            self.log_callback("No server is currently running.")
            return

        try:
            self.server_running = False

            if self.clients:
                disconnection_message = json.dumps({"type": "server_stopped", "path": "Server has been stopped."}).encode("utf-8")
                for client in self.clients:
                    try:
                        client.sendall(disconnection_message)
                    except Exception as e:
                        self.log_callback(f"Error notifying client: {e}")

                # Close all client sockets
                for client in self.clients:
                    try:
                        client.close()
                    except Exception as e:
                        self.log_callback(f"Error disconnecting client: {e}")
                self.clients.clear()
                self.log_callback("All connected clients have been disconnected.")
            else:
                self.log_callback("No clients were connected.")

            # close the server socket
            self.server_socket.close()
            self.server_socket = None
            self.log_callback("Server stopped.")

            # Wait for the accept_clients thread to exit
            if hasattr(self, 'accept_thread'):
                self.accept_thread.join()
        except Exception as e:
            self.log_callback(f"Error stopping server: {e}")


    # Accept client connections
    def accept_clients(self):
        while self.server_running:
            try:
                self.server_socket.settimeout(1.0)  # Timeout to periodically check self.server_running
                client_socket, addr = self.server_socket.accept()
                self.clients.append(client_socket)

                # Check if this is the first client
                if len(self.clients) == 1:
                    self.log_callback(f"Client connected: {addr}")
                else:
                    self.log_callback(f"New client connected: {addr}")

                # Start a thread to handle communication with this client
                threading.Thread(target=self.handle_client, args=(client_socket, addr), daemon=True).start()
            except socket.timeout:
                continue
            except Exception as e:
                if self.server_running:
                    self.log_callback(f"Error accepting client: {e}")




    # Handle communication with a client
    def handle_client(self, client_socket, client_address):
        try:
            while self.server_running:
                try:
                    data = client_socket.recv(1024)
                    if not data:
                        # Client disconnected unexpectedly
                        self.log_callback(f"Client disconnected: {client_address}")
                        break

                    # Process the received data
                    message = json.loads(data.decode("utf-8"))
                    message_type = message.get("type", "Unknown")

                    if message_type == "disconnect":
                        self.log_callback(f"Client requested disconnect: {client_address}")
                        break

                    # Log other messages from the client
                    self.log_callback(f"Received from {client_address}: {message}")
                except (ConnectionResetError, BrokenPipeError):
                    self.log_callback(f"Client forcibly disconnected: {client_address}")
                    break
                except json.JSONDecodeError as e:
                    self.log_callback(f"Error decoding JSON from {client_address}: {e}")
                    break
        except Exception as e:
            self.log_callback(f"Error handling client {client_address}: {e}")
        finally:
            client_socket.close()
            if client_socket in self.clients:
                self.clients.remove(client_socket)


    # Broadcast messages to all connected clients
    def broadcast_to_clients(self, message):
        if "path" not in message:
            message["path"] = "Unknown" 
        for client in self.clients:
            try:
                client.sendall(json.dumps(message).encode('utf-8'))
            except:
                self.clients.remove(client)




class FolderChangeHandler(FileSystemEventHandler):
    def __init__(self, log_callback, broadcast_callback):
        super().__init__()
        self.log_callback = log_callback
        self.broadcast_callback = broadcast_callback

    def on_created(self, event):
        if event.is_directory:
            message = {"type": "folder_added", "path": event.src_path}
            self.log_callback(f"Folder Added: {event.src_path}")
        else:
            message = {"type": "file_added", "path": event.src_path}
            self.log_callback(f"File Added: {event.src_path}")
        self.broadcast_callback(message)

    def on_deleted(self, event):
        if event.is_directory:
            message = {"type": "folder_deleted", "path": event.src_path}
            self.log_callback(f"Folder Deleted: {event.src_path}")
        else:
            message = {"type": "file_deleted", "path": event.src_path}
            self.log_callback(f"File Deleted: {event.src_path}")
        self.broadcast_callback(message)
