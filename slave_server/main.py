import threading

from src.Connexion import Connexion

def main():
    slave = Connexion("127.0.0.1", 12350)
    slave.connect()
    slave.send_data({"type": "slave", "content": "Hello World!"})

if __name__ == '__main__':
    main()