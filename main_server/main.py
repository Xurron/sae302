import threading
import argparse

from src.Connexion import Connexion

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Lancer le programme avec des arguments.')
    parser.add_argument('--ip', type=str, required=True, help='Adresse IP du serveur')
    parser.add_argument('--port', type=int, required=True, help='Port du serveur')
    parser.add_argument('--max-process', type=int, required=True, help='Nombre maximum de processus')

    args = parser.parse_args()
    print(args)

    print(f"Initialisation du serveur pour les clients")
    server = Connexion(args.ip, args.port, args.max_process)
    server_thread = threading.Thread(target=server.start)

    print(f"Démarrage du serveur maître")
    server_thread.start()