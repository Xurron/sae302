import threading

from src.Connexion import Connexion

def main():
    slave = Connexion("127.0.0.1", 10002, "slave")
    slave.connect()
    #slave.send_data({"type": "slave", "content": "Hello World!"})

if __name__ == '__main__':
    main()