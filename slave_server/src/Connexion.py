import shutil
import socket
import sys
import threading
import uuid
import json
import os
import subprocess

class Connexion:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.type = "slave"
        self.uid = str(uuid.uuid4())
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running = True
        self.receive_thread = None

    def connect(self):
        try:
            self.client_socket.connect((self.host, self.port))
            print(f"Connecté au serveur {self.host}:{self.port} en tant que \"{self.type}\" et ayant comme UID : {self.uid}")
            java_state = self.verif_java(False)
            c_state = self.verif_c(False)
            cpp_state = self.verif_cpp(False)
            data_connexion = {
                "author_type": "slave",
                "destination_type": "master",
                "type": "connexion",
                "uid": self.uid,
                "python": True,
                "java": java_state,
                "c": c_state,
                "c++": cpp_state
            }
            self.client_socket.send(json.dumps(data_connexion).encode('utf-8'))
            self.running = True
            self.__clear_tmp_directory() # supprimer les fichiers temporaires
            self.receive_thread = threading.Thread(target=self.receive_messages).start()
        except Exception as e:
            print(f"Une erreur est survenue lors de la connexion au serveur maître : {e}")

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
        if message["author_type"] == "master" and message["destination_type"] == "slave" and message["type"] == "file" and message["uid_destination"] == self.uid:
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
            ext = file_name.split(".")[-1]
            # faire un execute_file dans un thread
            threading.Thread(target=self.execute_file, args=(file_path, ext)).start()
        else:
            pass

    def send_data(self, message):
        if self.running:
            # vérifier que le message est bien un dictionnaire
            if isinstance(message, dict):
                try:
                    self.client_socket.send(json.dumps(message).encode('utf-8'))
                except Exception as e:
                    print(f"Une erreur est survenue lors de l'envoi du message : {message}, erreur : {e}")

    def execute_file(self, file_path: str, ext:str):
        if self.running:
            try:
                # exécuter le programme en fonction de l'extension
                if ext == "py":
                    try:
                        result = subprocess.run(["py", file_path], capture_output=True, text=True)
                    except:
                        result = subprocess.run(["python3", file_path], capture_output=True, text=True)
                elif ext == "java":
                    if self.verif_java(True):
                        result = subprocess.run(["java", file_path], capture_output=True, text=True)
                elif ext == "c":
                    if self.verif_c(True):
                        self.remove_compile_if_exist(f"./{file_path.split('.')[0]}")
                        os.system(f"gcc {file_path} -o {file_path.split('.')[0]}")
                        result = subprocess.run([f"./{file_path.split('.')[0]}"], capture_output=True, text=True)
                elif ext == "cpp":
                    if self.verif_cpp(True):
                        self.remove_compile_if_exist(f"./{file_path.split('.')[0]}")
                        os.system(f"g++ {file_path} -o {file_path.split('.')[0]}")
                        result = subprocess.run([f"./{file_path.split('.')[0]}"], capture_output=True, text=True)
                else:
                    print(f"Erreur : {ext} n'est pas une extension supportée.")

                if result:
                    print(result)
                    uid_exec = file_path.split('/')[-2]
                    if result.returncode == 0:
                        output = str(result.stdout)
                        message = {
                            "author_type": "slave",
                            "destination_type": "master",
                            "type": "output_file",
                            "uid": uid_exec,
                            "uid_slave": self.uid,
                            "error": False,
                            "output": output
                        }
                        self.send_data(message)
                        print(f"Le fichier {uid_exec} a bien été exécuté et a retourné : {output}")
                    else:
                        output = str(result.stderr)
                        message = {
                            "author_type": "slave",
                            "destination_type": "master",
                            "type": "output_file",
                            "uid": uid_exec,
                            "uid_slave": self.uid,
                            "error": True,
                            "output": output
                        }
                        self.send_data(message)
                        print(f"Une erreur est survenue lors de l'exécution du fichier : {file_path}")

                sys.exit(0)

            # filtrer l'erreur si la variable result n'existe pas
            except UnboundLocalError:
                uid_exec = file_path.split('/')[-2]
                message = {
                    "author_type": "slave",
                    "destination_type": "master",
                    "type": "output_file",
                    "uid": uid_exec,
                    "uid_slave": self.uid,
                    "error": True,
                    "output": "Une erreur est survenue lors de l'exécution du fichier, merci de vous référer à la console du serveur esclave."
                }
                self.send_data(message)
                print(f"Une erreur est survenue lors de l'exécution du fichier : {file_path}")

            except Exception as e:
                uid_exec = file_path.split('/')[-2]
                message = {
                    "author_type": "slave",
                    "destination_type": "master",
                    "type": "output_file",
                    "uid": uid_exec,
                    "uid_slave": self.uid,
                    "error": True,
                    "output": "Une erreur est survenue lors de l'exécution du fichier, merci de vous référer à la console du serveur esclave."
                }
                self.send_data(message)
                print(f"Une erreur est survenue lors de l'exécution du fichier : {file_path}, erreur : {e}")

    def remove_compile_if_exist(self, file):
        if os.path.exists(file):
            os.remove(file)

    # créer une fonction permettant de vérifier si java est installé ou non
    def verif_java(self, print_error: bool):
        try:
            subprocess.run(["java", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except FileNotFoundError:
            if print_error:
                print("Erreur lors de l'exécution d'un fichier écrit en Java : Java n'est pas installé.")
            return False

    def verif_c(self, print_error: bool):
        try:
            subprocess.run(["gcc", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except FileNotFoundError:
            if print_error:
                print("Erreur lors de l'exécution d'un fichier écrit en C : gcc n'est pas installé.")
            return False

    def verif_cpp(self, print_error: bool):
        try:
            subprocess.run(["g++", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except FileNotFoundError:
            if print_error:
                print("Erreur lors de l'exécution d'un fichier écrit en C++ : g++ n'est pas installé.")
            return False

    def __clear_tmp_directory(self):
        # fonction permettant de vider le dossier temporaire
        tmp_directory = "tmp/"
        if os.path.exists(tmp_directory):
            shutil.rmtree(tmp_directory)
        os.makedirs(tmp_directory, exist_ok=True)
        print("Dossier temporaire vidé")