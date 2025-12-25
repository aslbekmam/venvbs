from PyQt5.QtWidgets import *

from salon_app.db_access import Db
from salon_app.ui.admin_window import AdminWindow
from salon_app.ui.client_window import ClientWindow


class LoginWindow(QDialog):
    def __init__(self, db: Db):
        super().__init__()
        self.db = db
        self.next_window = None

        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)

        form = QFormLayout()
        form.addRow("Логин", self.username_input)
        form.addRow("Пароль", self.password_input)

        login_button = QPushButton("Войти")
        exit_button = QPushButton("Выход")
        login_button.clicked.connect(self._on_login)
        exit_button.clicked.connect(self.reject)

        actions = QHBoxLayout()
        actions.addStretch(1)
        actions.addWidget(login_button)
        actions.addWidget(exit_button)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Авторизация"))
        layout.addLayout(form)
        layout.addLayout(actions)
        self.setLayout(layout)

        self.setWindowTitle("Вход")
        self.setMinimumSize(360, 180)

        self.username_input.returnPressed.connect(self._on_login)
        self.password_input.returnPressed.connect(self._on_login)
        self.username_input.setFocus()

    def _on_login(self) -> None:
        username = self.username_input.text().strip()
        password = self.password_input.text()
        if not username or not password:
            QMessageBox.warning(self, "Ошибка", "Введите логин и пароль")
            return

        user = self.db.authenticate(username, password)
        if user is None:
            QMessageBox.critical(self, "Ошибка", "Неверный логин или пароль")
            return

        if user.role == "admin":
            self.next_window = AdminWindow(self.db, user)
        else:
            self.next_window = ClientWindow(self.db, user)

        self.next_window.show()
        self.accept()