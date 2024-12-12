import threading
from time import sleep
import os

from src.Connexion import Connexion

def main():
    print(f"Initialisation du serveur pour les clients")
    server = Connexion("127.0.0.1", 10002)
    server_thread = threading.Thread(target=server.start)

    print(f"Démarrage du serveur maître")
    server_thread.start()

    #while True:
    #    # si il y a un fichier main.py dans le dossier tmp, on l'envoi vers un serveur esclave
    #    if os.path.exists("tmp/main.py"):
    #        server.send_file("tmp/main.py")
    #        print(f"Envoi du fichier main.py à un esclave")
    #    sleep(10)

if __name__ == '__main__':
    main()