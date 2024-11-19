import threading
from time import sleep

from src.Connexion import Connexion

def main():
    client = Connexion("127.0.0.1", 12350, "client")
    client.connect()

    test = {
        "author_type": "client",
        "type": "message",
        "content": "Hello World!"
    }

    #client.send_data(test)
    #while True:
    #    client.send_data(test)
    #    sleep(2)

    client.send_file("project/Main.java")

if __name__ == '__main__':
    main()