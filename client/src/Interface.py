from PyQt6.QtCore import *
from PyQt6.QtWidgets import *

class Interface(QMainWindow):
    def __init__(self, client):
        super().__init__()
        self.client = client

        self.widget = QWidget()
        self.setCentralWidget(self.widget)

        self.grid = QGridLayout()
        self.widget.setLayout(self.grid)

        self.setWindowTitle("Exécution de programme")
        self.resize(800, 400)

        # créer un texte pour l'explication de l'interface
        self.explanation = QLabel("Pour pouvoir exécuter des programmes sur des serveurs esclaves il faut cliquer sur \"Sélectionnez un fichier à envoyer\".<br>Pour voir le résultat du programme exécuté, double cliquez sur le fichier envoyé.<br>Une indication est ajoutée pour savoir si le programme s'est exécuté correctement (✅ ; ⏳ ; ❌).<br>Pour voir la liste des clients et des serveurs esclaves connectés, cliquez sur \"Liste des clients et serveurs connectés\".")
        self.explanation.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.grid.addWidget(self.explanation, 0, 0, 1, 3)

        # créer un bouton pour sélectionner et envoyer un fichier
        self.file_button = QPushButton("Sélectionner un fichier à envoyer")
        self.file_button.clicked.connect(self.__select_file)
        self.grid.addWidget(self.file_button, 1, 0, 1, 3)

        # liste des fichiers envoyés
        self.file_list = QListWidget()
        self.file_list.itemDoubleClicked.connect(self.__show_file_details)
        self.grid.addWidget(self.file_list, 2, 0, 1, 3)

        # démarrer le rafraîchissement automatique
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.__refresh_file_list)
        self.refresh_timer.start(1000 * 1)  # rafraîchir la liste toutes les secondes

        self.server_button = QPushButton("Liste des clients et serveurs connectés")
        self.server_button.clicked.connect(self.__show_server_list)
        self.grid.addWidget(self.server_button, 3, 0, 1, 3)

    def __select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Sélectionner un fichier")
        if file_path:
            self.client._Connexion__send_file(file_path)
            self.__refresh_file_list()

    def __refresh_file_list(self):
        # rafraîchir la liste des fichiers envoyés
        self.file_list.clear()
        for file_info in self.client._Connexion__get_sent_files():
            if file_info["state"] == "ok":
                state = "✅"
            elif file_info["state"] == "sent":
                state = "⏳"
            else:
                state = "❌"

            item = QListWidgetItem(f"{state}・{file_info['uid']} - {file_info['file_path']}")
            item.setData(Qt.ItemDataRole.UserRole, file_info)
            self.file_list.addItem(item)

    def __show_file_details(self, item):
        file_info = item.data(Qt.ItemDataRole.UserRole)
        details_dialog = QDialog(self)
        details_dialog.setWindowTitle(f"Détails du fichier {file_info['file_path']}")

        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"UID: {file_info['uid']}"))
        layout.addWidget(QLabel(f"Chemin du fichier : {file_info['file_path']}"))

        try:
            layout.addWidget(QLabel(f"UID du slave : {file_info['uid_slave']}"))
        except KeyError:
            layout.addWidget(QLabel("UID du slave : Non disponible"))

        try:
            layout.addWidget(QLabel(f"Résultat : {file_info['output']}"))
        except KeyError:
            layout.addWidget(QLabel("Résultat : Non disponible"))

        details_dialog.setLayout(layout)
        details_dialog.exec()

    def __show_server_list(self):
        server_list = self.client._Connexion__get_server_connected()
        server_dialog = QDialog(self)
        server_dialog.setWindowTitle("Liste des clients & serveurs connectés")

        layout = QVBoxLayout()
        for server in server_list:
            if server["type"] == "client":
                layout.addWidget(QLabel(f"Client connecté : {server['uid']}"))
            elif server["type"] == "slave":
                layout.addWidget(QLabel(f"Serveur maître connecté : {server['uid']}"))
                layout.addWidget(QLabel(f"Langages disponibles : Python {"✅" if server["python"] else "❌"}, Java {"✅" if server["java"] else "❌"}, C {"✅" if server["c"] else "❌"}, C++ {"✅" if server["c++"] else "❌"}."))

            # ajouter une ligne vide pour séparer les clients et les serveurs
            layout.addWidget(QLabel(""))

        server_dialog.setLayout(layout)
        server_dialog.exec()