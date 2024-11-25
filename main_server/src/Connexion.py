import json
import shutil
import socket
import threading
import os

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
        self.__clear_tmp_directory() # supprimer les fichiers temporaires
        self.accept_clients()

    def accept_clients(self):
        while self.running:
            client_socket, client_address = self.server_socket.accept()
            client_type = self.get_client_type(client_socket)
            if client_type["type"] == "connexion" and client_type["author_type"] == "client":
                content_author_type = client_type["author_type"]
                content_destination_type = client_type["destination_type"]
                content_uid = client_type["uid"]

                content = {
                    "author_type": content_author_type,
                    "destination_type": content_destination_type,
                    "uid": content_uid,
                    "socket": client_socket
                }

                self.clients.append(content)
                threading.Thread(target=self.handle_client, args=(client_socket,)).start()

            if client_type["type"] == "connexion" and client_type["author_type"] == "slave":
                content_author_type = client_type["author_type"]
                content_destination_type = client_type["destination_type"]
                content_uid = client_type["uid"]
                content_python = client_type["python"]
                content_java = client_type["java"]
                content_c = client_type["c"]
                content_cpp = client_type["c++"]

                content = {
                    "author_type": content_author_type,
                    "destination_type": content_destination_type,
                    "uid": content_uid,
                    "socket": client_socket,
                    "files": 0,
                    "python": content_python,
                    "java": content_java,
                    "c": content_c,
                    "c++": content_cpp
                }

                self.clients.append(content)
                threading.Thread(target=self.handle_client, args=(client_socket,)).start()

            print(f"Connexion établie avec {client_address}")

    def get_client_type(self, client_socket):
        client_type = client_socket.recv(1024).decode('utf-8')
        client_type = json.loads(client_type)
        return client_type

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
        # va déterminer si c'est un fichier ou non envoyé par le client pour le master
        if message["author_type"] == "client" and message["destination_type"] == "master" and message["type"] == "file":
            uid = message["uid"]
            file_name = message["file_name"]
            file_content = message["file_content"].encode('latin-1')
            file_path = f"tmp/{uid}/"
            # créer le dossier tmp/uid
            os.makedirs(file_path, exist_ok=True)
            file_path = f"tmp/{uid}/" + file_name
            with open(file_path, 'wb') as file:
                file.write(file_content)
            print(f"Un fichier a bien été reçu : {file_path}")
            self.dispatch(file_path, uid)
        else:
            if message["author_type"] == "client":
                print(f"Message reçu d'un client, {message}")
            if message["author_type"] == "slave":
                print(f"Message reçu d'un esclave, {message}")

    #def broadcast(self, message, client_socket):
    #    for client in self.clients:
    #        if client != client_socket:
    #            try:
    #                client.send(message.encode('utf-8'))
    #            except:
    #                pass

    def remove_client(self, client_socket):
        if client_socket in self.clients:
            print(f"Déconnexion : {client_socket}")
            self.clients.remove(client_socket)
            client_socket.close()

    def send_data(self, message):
        if self.running:
            if isinstance(message, dict):
                try:
                    self.server_socket.send(json.dumps(message).encode('utf-8'))
                    print(f"Sent: {message}")
                except Exception as e:
                    print(f"Error sending message: {message}")

    def send_file(self, uid_slave, uid_file, file_path):
        # fonction permettant d'envoyer des fichiers (qui iront vers les slaves)
        if self.running:
            try:
                file_name = file_path.split('/')[-1]
                with open(file_path, 'rb') as file:
                    file_content = file.read()
                    message = {
                        "author_type": "master",
                        "destination_type": "slave",
                        "uid": uid,
                        "type": "file",
                        "file_name": file_name,
                        "file_content": file_content.decode('utf-8')
                    }
                    self.send_data(message)
                    print(f"Fichier envoyé : {file_path}")
            except Exception as e:
                print(f"Erreur lors de l'envoi du fichier : {file_path}, erreur: {e}")

    # faire une fonction pour la répartition de charge
    def dispatch(self, file_path, uid):
        # récupérer le type de fichier reçu avec l'extension (ex: .py)
        # récupérer la liste des slaves connectés
        # faire une liste des slaves permettant d'exécuter le fichier
        # récupérer le nombre de fichiers déjà envoyés à chaque slave
        # envoyer le fichier au slave avec le moins de fichiers

        # récupérer l'extension du fichier
        ext = file_path.split(".")[-1]

        # récupérer la liste des slaves connectés
        slaves = []
        for client in self.clients:
            if client["author_type"] == "slave":
                slaves.append(client)

        # faire une liste des slaves permettant d'exécuter le fichier
        slaves_exec = []

        for slave in slaves:
            if ext == "py" and slave["python"]:
                slaves_exec.append(slave)
            elif ext == "java" and slave["java"]:
                slaves_exec.append(slave)
            elif ext == "c" and slave["c"]:
                slaves_exec.append(slave)
            elif ext == "cpp" and slave["c++"]:
                slaves_exec.append(slave)

        # récupérer le nombre de fichiers déjà envoyés à chaque slave
        #files_sent = []
        #for slave in slaves_exec:
        #    files_sent.append(len(slave["files"]))

        # si aucun slave ne peut exécuter le fichier, envoyer un message d'erreur
        if not slaves_exec:
            print("Aucun esclave ne peut exécuter le fichier")
            return

        # envoyer le fichier au slave avec le moins de fichiers (réécrire cette section entièrement)
        # récupérer le slave qui a envoyé le moins de message (tout en gardant toutes les informations concernant le slave)
        # envoyer un fichier à ce slave en récupérant le fichier à envoyer (le fichier est envoyé dans le dossier tmp/uid)
        # incrémenter le nombre de fichiers envoyés à ce slave

        # récupérer le slave qui a envoyé le moins de message (tout en gardant toutes les informations concernant le slave)
        min_slave = None
        for slave in slaves_exec:
            if min_slave is None:
                min_slave = slave
            if slave["files"] < min_slave["files"]:
                min_slave = slave

    def __clear_tmp_directory(self):
        # fonction permettant de vider le dossier temporaire
        tmp_directory = "tmp/"
        if os.path.exists(tmp_directory):
            shutil.rmtree(tmp_directory)
        os.makedirs(tmp_directory, exist_ok=True)
        print("Dossier temporaire vidé")