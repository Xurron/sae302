import signal
import sys
import threading
from time import sleep

from src.Connexion import Connexion

def procedure_deconnexion(sig, frame):
    client.disconnect()
    sys.exit(0)

if __name__ == '__main__':
    client = Connexion("127.0.0.1", 10002, "client")
    client.connect()

    # envoi de fichier (dans le futur envoi de requête)
    client.send_file("project/main.py")

    # Enregistrez le signal d'interruption clavier (CTRL+C)
    signal.signal(signal.SIGINT, procedure_deconnexion)