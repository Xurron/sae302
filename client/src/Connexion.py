import json
import socket
import threading
import uuid

class Connexion:
    def __init__(self, host: str, port: int, type: str):
        self.host = host
        self.port = port
        self.type = type
        self.uid = str(uuid.uuid4())
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running = False
        self.receive_thread = None

    def connect(self):
        try:
            self.client_socket.connect((self.host, self.port))
            print(f"Connecté au serveur {self.host}:{self.port} en tant que \"{self.type}\"")
            data_connexion = {
                "author_type": "client",
                "destination_type": "master",
                "type": "connexion",
                "uid": self.uid
            }
            self.client_socket.send(json.dumps(data_connexion).encode('utf-8'))
            self.running = True
            self.receive_thread = threading.Thread(target=self.receive_messages).start()
        except Exception as e:
            print(f"Connection error: {e}")

    def disconnect(self):
        if self.running:
            print(f"Déconnexion du serveur {self.host}:{self.port}")
            self.running = False
            self.client_socket.close()
            if self.receive_thread is not None:
                self.receive_thread.join()

    def receive_messages(self):
        while self.running:
            try:
                message = self.client_socket.recv(1024).decode('utf-8')
                if message:
                    print(f"Received: {message}")
                else:
                    break
            except:
                break

    def send_data(self, message):
        if self.running:
            # vérifier que le message est bien un dictionnaire
            if isinstance(message, dict):
                try:
                    self.client_socket.send(json.dumps(message).encode('utf-8'))
                    print(f"Sent: {message}")
                except Exception as e:
                    print(f"Error sending message: {message}, error: {e}")

    def send_file(self, file_path):
        if self.running:
            try:
                uid = str(uuid.uuid4())
                file_name = file_path.split('/')[-1]
                with open(file_path, 'rb') as file:
                    file_content = file.read()
                    message = {
                        "author_type": "client",
                        "destination_type": "master",
                        "uid": uid,
                        "type": "file",
                        "file_name": file_name,
                        "file_content": file_content.decode('utf-8')
                    }
                    self.client_socket.send(json.dumps(message).encode('utf-8'))
                    print(f"Fichier envoyé : {file_path}")
                    print(message)
            except Exception as e:
                print(f"Error sending file: {file_path}, error: {e}")