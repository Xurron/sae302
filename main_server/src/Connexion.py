import json
import socket
import threading

#from main_server.src.ConnexionSlave import ConnexionSlave
from .ConnexionSlave import ConnexionSlave

# classe permettant aux clients de se connecter au serveur principal
# va permettre l'échange des informations reçu par les serveurs esclaves et de les envoyer aux clients

class Connexion:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients = []
        self.running = True

    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"Le serveur a démarré sur {self.host}:{self.port}")
        self.accept_clients()

    def accept_clients(self):
        while self.running:
            client_socket, client_address = self.server_socket.accept()
            print(f"Connexion : {client_address}")
            client_type = self.get_client_type(client_socket)
            self.clients.append({'socket': client_socket, 'type': client_type})
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()
            self.thread_received_file = threading.Thread(target=self.receive_file)
            self.thread_received_file.start()

    def get_client_type(self, client_socket):
        client_socket.send("Please send your client type".encode('utf-8'))
        client_type = client_socket.recv(1024).decode('utf-8')
        return client_type

    # fonction permettant de gérer les messages reçus par les clients
    def handle_client(self, client_socket):
        while self.running:
            try:
                message = client_socket.recv(1024).decode('utf-8')
                if message:
                    msg = json.loads(message)
                    self.traitement_message(msg, client_socket)
                else:
                    self.remove_client(client_socket)
                    break
            except:
                pass

    def traitement_message(self, message, client_socket):
        if message["author_type"] == "client":
            print(f"Message reçu d'un client, {message}")
        if message["author_type"] == "slave":
            print(f"Message reçu d'un esclave, {message}")

    def broadcast(self, message, client_socket):
        for client in self.clients:
            if client != client_socket:
                try:
                    client.send(message.encode('utf-8'))
                except:
                    pass

    def remove_client(self, client_socket):
        if client_socket in self.clients:
            print(f"Déconnexion : {client_socket}")
            self.clients.remove(client_socket)
            client_socket.close()