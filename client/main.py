import argparse
import signal
import sys

from PyQt6.QtWidgets import *

from src.Connexion import Connexion
from src.Interface import Interface

def procedure_deconnexion(sig, frame):
    client.disconnect()
    sys.exit(0)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Lancer le programme avec des arguments.')
    parser.add_argument('--ip', type=str, required=True, help='Adresse IP du serveur')
    parser.add_argument('--port', type=int, required=True, help='Port du serveur')

    args = parser.parse_args()

    client = Connexion(args.ip, args.port)
    client.connect()

    if client.running:
        app = QApplication(sys.argv)
        interface = Interface(client)
        interface.show()
        app.exec()
    else:
        print(f"Une erreur est survenue lors de la connexion au serveur")
        sys.exit(0)

    # Enregistrez le signal d'interruption clavier (CTRL+C)
    signal.signal(signal.SIGINT, procedure_deconnexion)