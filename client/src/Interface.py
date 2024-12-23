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

        # définition du nombre de processus maximum pouvant être exécuté par les slaves
        self.max_process = QLabel("Nombre de processus maximum :")
        self.grid.addWidget(self.max_process, 0, 0)

        self.max_process_input = QLineEdit()
        self.grid.addWidget(self.max_process_input, 0, 1)

        self.max_process_button = QPushButton("Définir le nombre de processus")
        self.max_process_button.clicked.connect(self.__set_max_process)
        self.grid.addWidget(self.max_process_button, 0, 2)

        # créer un bouton pour sélectionner et envoyer un fichier
        self.file_button = QPushButton("Sélectionner un fichier à envoyer")
        self.file_button.clicked.connect(self.__select_file)
        self.grid.addWidget(self.file_button, 1, 0)

        # faire un layout pour afficher les fichiers envoyés et quand on sélectionne un fichier, on peut voir le slave qui l'a exécuté et le résultat retourné
        # il doit y avoir une liste de fichiers envoyés avec l'UID du process et le chemin du fichier
        # pour chaque fichier, on doit pouvoir double cliquer dessus pour avoir une nouvelle fenêtre pour avoir le résultat retourné par le slave et autres informations
        # le rafraichissement doit être automatique

        # liste des fichiers envoyés
        self.file_list = QListWidget()
        self.file_list.itemDoubleClicked.connect(self.__show_file_details)
        self.grid.addWidget(self.file_list, 2, 0, 1, 3)

        # démarrer le rafraîchissement automatique
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.__refresh_file_list)
        self.refresh_timer.start(5000)  # rafraîchir toutes les 5 secondes

    def __set_max_process(self):
        max_process = self.max_process_input.text()
        # self.client.set_max_process(max_process)

    def __select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Sélectionner un fichier")
        if file_path:
            self.client.send_file(file_path)

    def __refresh_file_list(self):
        # rafraîchir la liste des fichiers envoyés
        self.file_list.clear()
        for file_info in self.client.get_sent_files():
            if file_info["state"] == "ok":
                state = "✅"
            elif file_info["state"] == "sent":
                state = "⏳" # à changer
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
        layout.addWidget(QLabel(f"Chemin du fichier: {file_info['file_path']}"))

        try:
            layout.addWidget(QLabel(f"UID du slave: {file_info['uid_slave']}"))
        except KeyError:
            layout.addWidget(QLabel("UID du slave: Non disponible"))

        try:
            layout.addWidget(QLabel(f"Résultat: {file_info['output']}"))
        except KeyError:
            layout.addWidget(QLabel("Résultat: Non disponible"))

        details_dialog.setLayout(layout)
        details_dialog.exec()