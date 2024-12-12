import socket
import threading
import uuid
import json
import os

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
            # récupérer les valeurs à mettre dans les langages de possibles
            data_connexion = {
                "author_type": "slave",
                "destination_type": "master",
                "type": "connexion",
                "uid": self.uid,
                "python": True,
                "java": True,
                "c": True,
                "c++": True
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
                    msg = json.loads(message)
                    self.traitement_message(msg)
                else:
                    break
            except:
                pass

    def traitement_message(self, message):
        # va déterminer si c'est un fichier ou non envoyé par le client pour le master
        if message["author_type"] == "master" and message["destination_type"] == "master" and message["type"] == "file":
            uid_file = message["uid_file"]
            file_name = message["file_name"]
            file_content = message["file_content"].encode('latin-1')
            file_path = f"tmp/{uid_file}/"
            # créer le dossier tmp/uid
            os.makedirs(file_path, exist_ok=True)
            file_path = f"tmp/{uid_file}/" + file_name
            with open(file_path, 'wb') as file:
                file.write(file_content)
            print(f"Un fichier a bien été reçu : {file_path}")
            self.send_file_to_slave(file_path)
        else:
            if message["author_type"] == "slave":
                print(f"Message reçu du serveur maître : {message}")

    def send_data(self, message):
        if self.running:
            # vérifier que le message est bien un dictionnaire
            if isinstance(message, dict):
                try:
                    self.client_socket.send(str(message).encode('utf-8'))
                    print(f"Sent: {message}")
                except:
                    print(f"Error sending message: {message}")