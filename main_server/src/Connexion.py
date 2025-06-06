import json
import shutil
import socket
import threading
import os

class Connexion:
    """
        Classe permettant de gérer la connexion entre le client et le serveur

        :param host: str : Adresse IP du serveur
        :type host: str
        :param port: int : Port du serveur
        :type port: int
        :param max_process: int : Nombre maximum de processus
        :type max_process: int
    """
    def __init__(self, host: str, port: int, max_process: int):
        """
            Constructeur de la classe Connexion
        """
        self.host = host
        self.port = port
        self.__server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__clients = []
        self.__running = True
        self.__max_process = max_process

    def start(self):
        """
            Méthode permettant de démarrer le serveur maître
        """
        self.__server_socket.bind((self.host, self.port))
        self.__server_socket.listen(5)
        print(f"Le serveur a démarré sur {self.host}:{self.port}")
        self.__clear_tmp_directory() # supprimer les fichiers temporaires
        self.__accept_clients()

    def __accept_clients(self):
        while self.__running:
            client_socket, client_address = self.__server_socket.accept()
            client_type = self.__get_client_type(client_socket)
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

                self.__clients.append(content)
                threading.Thread(target=self.__handle_client, args=(client_socket,)).start()
                print(f"Connexion établie avec le client {client_address}")

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
                    "process_running": 0,
                    "python": content_python,
                    "java": content_java,
                    "c": content_c,
                    "c++": content_cpp
                }

                self.__clients.append(content)
                threading.Thread(target=self.__handle_client, args=(client_socket,)).start()
                print(f"Connexion établie avec le serveur esclave {client_address}")

    def __get_client_type(self, client_socket):
        client_type = client_socket.recv(1024).decode('utf-8')
        client_type = json.loads(client_type)
        return client_type

    def __handle_client(self, client_socket):
        while self.__running:
            try:
                message = client_socket.recv(1024).decode('utf-8')
                if message:
                    msg = json.loads(message)
                    self.__traitement_message(msg, client_socket)
                else:
                    self.__remove_client(client_socket)
                    break
            except:
                pass

    def __traitement_message(self, message, client_socket):
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
            self.__send_file_to_slave(file_path)
        elif message["author_type"] == "slave" and message["destination_type"] == "master" and message["type"] == "output_file":
            uid = message["uid"]
            uid_slave = message["uid_slave"]
            output = message["output"]
            error = message["error"]
            message = {
                "author_type": "master",
                "destination_type": "client",
                "type": "output_file",
                "uid_slave": uid_slave,
                "uid": uid,
                "error": error,
                "output": output
            }

            for slave in self.__clients:
                if slave["uid"] == uid_slave:
                    slave["process_running"] -= 1

            self.__send_data(message)
        elif message["author_type"] == "client" and message["destination_type"] == "master" and message["type"] == "request_server_connected":
            self.__send_server_connected()
        else:
            pass

    def __broadcast(self, message):
        for client in self.__clients:
            c = client["socket"]
            try:
                c.send(message.encode('utf-8'))
            except:
                pass

    def __remove_client(self, client_socket):
        for clients in self.__clients:
            if clients["socket"] == client_socket:
                print(f"Déconnexion : {client_socket}")
                self.__clients.remove(clients)
                client_socket.close()

    def __send_data(self, message):
        if self.__running:
            # vérifier que le message est bien un dictionnaire
            if isinstance(message, dict):
                try:
                    self.__broadcast(json.dumps(message))
                except Exception as e:
                    print(f"Une erreur est survenue lors de l'envoi du message : {message}, erreur: {e}")

    def __send_file_to_slave(self, file_path: str):
        # fonction permettant d'envoyer des données à un esclave
        global uid_slave

        if self.__running:
            try:
                # pour chaque slave connecté, on récupère celui qui a la valeur process_running la plus basse parmis ceux qui ont le type de fichier à exécuter (JAVA, python, c, c++) à True
                # puis on envoie le message à ce slave
                min_slave = None
                ext = file_path.split(".")[-1]
                if ext == "py":
                    ext = "python"
                elif ext == "java":
                    ext = "java"
                elif ext == "c":
                    ext = "c"
                elif ext == "cpp":
                    ext = "c++"
                else:
                    ext = None

                file_name = file_path.split('/')[-1]
                uid_file = file_path.split('/')[-2]

                if ext is None:
                    message = {
                        "author_type": "master",
                        "destination_type": "client",
                        "type": "output_file",
                        "uid": uid_file,
                        "error": True,
                        "output": "Extension de fichier non supportée"
                    }
                    self.__send_data(message)
                    return

                for slave in self.__clients:
                    if slave["author_type"] == "slave":
                        if min_slave is None:
                            if slave[ext] and slave["process_running"] < self.__max_process:
                                min_slave = slave
                        else:
                            if slave[ext] and slave["process_running"] < self.__max_process and slave["process_running"] < min_slave["process_running"]:
                                min_slave = slave

                # s'il n'y a aucun esclave qui peut exécuter le fichier, on envoie un message d'erreur au client
                if min_slave is None:
                    message = {
                        "author_type": "master",
                        "destination_type": "client",
                        "type": "output_file",
                        "uid": uid_file,
                        "error": True,
                        "output": "Aucun serveur esclave disponible pour exécuter le fichier"
                    }
                    self.__send_data(message)
                    return

                uid_slave = min_slave["uid"]

                with open(file_path, 'rb') as file:
                    file_content = file.read()
                    message = {
                        "author_type": "master",
                        "destination_type": "slave",
                        "uid_destination": uid_slave,
                        "uid_file": uid_file,
                        "type": "file",
                        "file_name": file_name,
                        "file_content": file_content.decode('utf-8')
                    }

                self.__send_data(message)
                min_slave["process_running"] += 1
            except Exception as e:
                print(f"Une erreur est survenue lors de l'envoi d'un fichier au serveur esclave ayant comme UID {uid_slave} : erreur : {e}")

    def __clear_tmp_directory(self):
        # fonction permettant de vider le dossier temporaire
        tmp_directory = "tmp/"
        if os.path.exists(tmp_directory):
            shutil.rmtree(tmp_directory)
        os.makedirs(tmp_directory, exist_ok=True)
        print("Dossier temporaire vidé")

    def __send_server_connected(self):
        # faire une variable pour self.__clients mais qui peut être envoyée dans un json
        clients = []
        for client in self.__clients:
            if client["author_type"] == "client":
                clients.append({
                    "type": "client",
                    "uid": client["uid"]
                })
            elif client["author_type"] == "slave":
                clients.append({
                    "type": "slave",
                    "uid": client["uid"],
                    "process_running": client["process_running"],
                    "python": client["python"],
                    "java": client["java"],
                    "c": client["c"],
                    "c++": client["c++"]
                })

        message = {
            "author_type": "master",
            "destination_type": "client",
            "type": "request_server_connected",
            "list": clients
        }
        self.__send_data(message)