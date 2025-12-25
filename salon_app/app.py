from PyQt5.QtWidgets import QApplication
from db import init_db
from salon_app.db_access import Db
from salon_app.ui.login_window import LoginWindow

def run() -> None:
    init_db(seed=True)

    app = QApplication([])
    db = Db()
    app.aboutToQuit.connect(db.close)

    login = LoginWindow(db)
    result = login.exec_()
    if result != login.Accepted:
        return
    app.exec_()