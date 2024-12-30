import json
import os
import shutil
import socket
import threading
import uuid
from time import sleep


class Connexion:
    """
        Classe permettant de gérer la connexion entre le client et le serveur

        :param host: str : Adresse IP du serveur
        :type host: str
        :param port: int : Port du serveur
        :type port: int
    """
    def __init__(self, host: str, port: int):
        """
            Constructeur de la classe Connexion
        """
        self.host = host
        self.port = port
        self.__type = "client"
        self.__uid = str(uuid.uuid4())
        self.__client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running = False
        self.__receive_thread = None
        self.__sent_file_array = []
        self.__server_connected = []
        self.__clear_tmp_directory()

    def connect(self):
        """
            Méthode permettant de se connecter au serveur maître
        """
        try:
            self.__client_socket.connect((self.host, self.port))
            print(f"Connecté au serveur {self.host}:{self.port} en tant que \"{self.__type}\"")
            data_connexion = {
                "author_type": "client",
                "destination_type": "master",
                "type": "connexion",
                "uid": self.__uid
            }
            self.__client_socket.send(json.dumps(data_connexion).encode('utf-8'))
            self.running = True
            self.__receive_thread = threading.Thread(target=self.__receive_messages).start()
        except Exception as e:
            print(f"Une erreur est survenue lors de la connexion au serveur maître : {e}")

    def disconnect(self):
        """
            Méthode permettant de se déconnecter du serveur
        """
        if self.running:
            print(f"Déconnexion du serveur {self.host}:{self.port}")
            self.running = False
            self.__client_socket.close()
            if self.__receive_thread is not None:
                self.__receive_thread.join()

    def __receive_messages(self):
        while self.running:
            try:
                message = self.__client_socket.recv(1024).decode('utf-8')
                if message:
                    msg = json.loads(message)
                    self.__traitement_message(msg)
                else:
                    break
            except:
                break

    def __traitement_message(self, message):
        # réception des messages pour la récupération de la sortie de l'exécution du programme
        if message["author_type"] == "master" and message["destination_type"] == "client" and message["type"] == "output_file":
            output = message["output"]
            uid = message["uid"]
            try:
                uid_slave = message["uid_slave"]
            except:
                uid_slave = None
            print(f"Pour le fichier ayant comme ID : {uid}, le contenu est : {output}")
            # enregistrer le fichier dans un dossier temporaire
            with open(f"tmp/{uid}.txt", "w") as file:
                file.write(output)
            # renseigner le résultat dans le tableau des fichiers envoyés (modifier le status et ajouter l'uid du slave & le résultat)
            for file in self.__sent_file_array:
                if file["uid"] == uid:
                    if message["error"]:
                        file["state"] = "ko"
                    else:
                        file["state"] = "ok"
                    file["output"] = output
                    file["uid_slave"] = uid_slave
                    break
        elif message["author_type"] == "master" and message["destination_type"] == "client" and message["type"] == "request_server_connected":
            self.__traitement_message_server_connected(message)

    def __send_data(self, message):
        if self.running:
            # vérifier que le message est bien un dictionnaire
            if isinstance(message, dict):
                try:
                    self.__client_socket.send(json.dumps(message).encode('utf-8'))
                except Exception as e:
                    print(f"Une erreur est survenue lors de l'envoi du message : {message}, erreur : {e}")

    def __send_file(self, file_path):
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
                    self.__client_socket.send(json.dumps(message).encode('utf-8'))
                    print(f"Fichier envoyé : {file_path} avec comme UID : {uid}")
                    log = {
                        "uid": uid,
                        "state": "sent",
                        "file_path": file_path
                    }
                    self.__sent_file_array.append(log)
            except Exception as e:
                print(f"Une erreur est survenue lors de l'envoi du fichier ayant comme chemin : {file_path}, erreur : {e}")

    def __get_sent_files(self):
        return self.__sent_file_array

    def __clear_tmp_directory(self):
        # fonction permettant de vider le dossier temporaire
        tmp_directory = "tmp/"
        if os.path.exists(tmp_directory):
            shutil.rmtree(tmp_directory)
        os.makedirs(tmp_directory, exist_ok=True)
        print("Dossier temporaire vidé")

    def __send_request_server_connected(self):
        message = {
            "author_type": "client",
            "destination_type": "master",
            "type": "request_server_connected"
        }
        self.__send_data(message)

    def __traitement_message_server_connected(self, message):
        list = message["list"]
        self.__server_connected = list

    def __get_server_connected(self):
        self.__send_request_server_connected()
        sleep(1)
        return self.__server_connected