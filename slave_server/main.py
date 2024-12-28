import argparse
import threading

from src.Connexion import Connexion

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Lancer le programme avec des arguments.')
    parser.add_argument('--ip', type=str, required=True, help='Adresse IP du serveur')
    parser.add_argument('--port', type=int, required=True, help='Port du serveur')

    args = parser.parse_args()

    slave = Connexion(args.ip, args.port)
    slave.connect()