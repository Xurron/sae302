import threading

from src.Connexion import Connexion
from src.ConnexionClient import ConnexionClient
from src.ConnexionSlave import ConnexionSlave

def main():
    print(f"Initialisation du serveur pour les clients")
    client_server = Connexion("127.0.0.1", 12350)
    client_thread = threading.Thread(target=client_server.start)

    #print(f"Initialisation du serveur pour les serveurs esclaves")
    #slave_server = ConnexionSlave("127.0.0.1", 23457)
    #server_thread = threading.Thread(target=slave_server.start)

    print(f"Démarrage des serveurs")
    client_thread.start()
    #server_thread.start()

if __name__ == '__main__':
    main()