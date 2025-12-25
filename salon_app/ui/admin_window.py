from datetime import date
from typing import Optional
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtWidgets import *

from salon_app.db_access import AuthUser, Db
from salon_app.ui.edit_dialogs import ClientEditDialog, MasterEditDialog, ServiceEditDialog
from salon_app.ui.table_helpers import clear_table, set_table_row


class AdminWindow(QMainWindow):
    def __init__(self, db: Db, user: AuthUser):
        super().__init__()
        self.db = db
        self.user = user

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.clients_tab = self._build_clients_tab()
        self.masters_tab = self._build_masters_tab()
        self.services_tab = self._build_services_tab()
        self.appointments_tab = self._build_appointments_tab()

        self.tabs.addTab(self.clients_tab, "Клиенты")
        self.tabs.addTab(self.masters_tab, "Мастера")
        self.tabs.addTab(self.services_tab, "Прайс")
        self.tabs.addTab(self.appointments_tab, "Записи")

        self.setWindowTitle("Администратор")
        self.setMinimumSize(980, 620)

        self._refresh_clients()
        self._refresh_masters()
        self._refresh_services()
        self._show_all_appointments()

    def _build_clients_tab(self) -> QWidget:
        root = QWidget()
        layout = QVBoxLayout(root)

        self.clients_table = QTableWidget(0, 6)
        self.clients_table.setHorizontalHeaderLabels(
            ["ID", "ФИО", "Дата рождения", "Телефон", "Email", "Регистрация"]
        )
        self.clients_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.clients_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.clients_table.verticalHeader().setVisible(False)
        self.clients_table.horizontalHeader().setStretchLastSection(True)

        actions = QHBoxLayout()
        add_button = QPushButton("Добавить")
        edit_button = QPushButton("Изменить")
        actions.addStretch(1)
        actions.addWidget(add_button)
        actions.addWidget(edit_button)

        add_button.clicked.connect(self._add_client)
        edit_button.clicked.connect(self._edit_client)

        layout.addLayout(actions)
        layout.addWidget(self.clients_table, 1)
        return root

    def _build_masters_tab(self) -> QWidget:
        root = QWidget()
        layout = QVBoxLayout(root)

        self.masters_table = QTableWidget(0, 6)
        self.masters_table.setHorizontalHeaderLabels(
            ["ID", "ФИО", "Специализация", "Телефон", "Email", "Дата найма"]
        )
        self.masters_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.masters_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.masters_table.verticalHeader().setVisible(False)
        self.masters_table.horizontalHeader().setStretchLastSection(True)

        actions = QHBoxLayout()
        add_button = QPushButton("Добавить")
        edit_button = QPushButton("Изменить")
        actions.addStretch(1)
        actions.addWidget(add_button)
        actions.addWidget(edit_button)

        add_button.clicked.connect(self._add_master)
        edit_button.clicked.connect(self._edit_master)

        layout.addLayout(actions)
        layout.addWidget(self.masters_table, 1)
        return root

    def _build_services_tab(self) -> QWidget:
        root = QWidget()
        layout = QVBoxLayout(root)

        self.services_table = QTableWidget(0, 5)
        self.services_table.setHorizontalHeaderLabels(
            ["ID", "Категория", "Услуга", "Цена", "Длительность"]
        )
        self.services_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.services_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.services_table.verticalHeader().setVisible(False)
        self.services_table.horizontalHeader().setStretchLastSection(True)

        actions = QHBoxLayout()
        add_button = QPushButton("Добавить")
        edit_button = QPushButton("Изменить")
        actions.addStretch(1)
        actions.addWidget(add_button)
        actions.addWidget(edit_button)

        add_button.clicked.connect(self._add_service)
        edit_button.clicked.connect(self._edit_service)

        layout.addLayout(actions)
        layout.addWidget(self.services_table, 1)
        return root

    def _build_appointments_tab(self) -> QWidget:
        root = QWidget()
        layout = QVBoxLayout(root)

        filter_row = QHBoxLayout()
        self.date_from = QDateEdit()
        self.date_to = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_to.setCalendarPopup(True)
        self.date_from.setDisplayFormat("yyyy-MM-dd")
        self.date_to.setDisplayFormat("yyyy-MM-dd")
        self.date_from.setDate(QDate.currentDate().addDays(-7))
        self.date_to.setDate(QDate.currentDate().addDays(7))

        filter_button = QPushButton("Фильтровать")
        show_all_button = QPushButton("Показать все")

        filter_row.addWidget(self.date_from)
        filter_row.addWidget(self.date_to)
        filter_row.addWidget(filter_button)
        filter_row.addWidget(show_all_button)
        filter_row.addStretch(1)

        filter_button.clicked.connect(self._filter_appointments)
        show_all_button.clicked.connect(self._show_all_appointments)

        self.appointments_table = QTableWidget(0, 8)
        self.appointments_table.setHorizontalHeaderLabels(
            ["ID", "Дата", "Время", "Статус", "Клиент", "Мастер", "Услуга", "Сумма"]
        )
        self.appointments_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.appointments_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.appointments_table.verticalHeader().setVisible(False)
        self.appointments_table.horizontalHeader().setStretchLastSection(True)

        layout.addLayout(filter_row)
        layout.addWidget(self.appointments_table, 1)
        return root

    def _selected_id(self, table: QTableWidget) -> Optional[int]:
        row = table.currentRow()
        if row < 0:
            return None
        item = table.item(row, 0)
        if item is None:
            return None
        try:
            return int(item.text())
        except ValueError:
            return None

    def _refresh_clients(self) -> None:
        clear_table(self.clients_table)
        rows = self.db.list_clients()
        for i, row in enumerate(rows):
            set_table_row(
                self.clients_table,
                i,
                [
                    str(row["id_client"]),
                    str(row["fio"] or ""),
                    str(row["birth_date"] or ""),
                    str(row["phone"] or ""),
                    str(row["email"] or ""),
                    str(row["registration_date"] or ""),
                ],
            )

    def _add_client(self) -> None:
        dialog = ClientEditDialog(self, title="Новый клиент")
        if dialog.exec_() != dialog.Accepted:
            return
        data = dialog.get_data()
        self.db.create_client(**data)
        self._refresh_clients()

    def _edit_client(self) -> None:
        id_client = self._selected_id(self.clients_table)
        if id_client is None:
            QMessageBox.information(self, "Инфо", "Выберите клиента")
            return

        current = None
        for row in self.db.list_clients():
            if int(row["id_client"]) == id_client:
                current = row
                break
        if current is None:
            return

        dialog = ClientEditDialog(
            self,
            title="Изменить клиента",
            fio=str(current["fio"] or ""),
            birth_date=str(current["birth_date"] or ""),
            phone=str(current["phone"] or ""),
            email=str(current["email"] or ""),
            registration_date=str(current["registration_date"] or ""),
        )
        if dialog.exec_() != dialog.Accepted:
            return
        data = dialog.get_data()
        self.db.update_client(id_client=id_client, **data)
        self._refresh_clients()

    def _refresh_masters(self) -> None:
        clear_table(self.masters_table)
        rows = self.db.list_masters()
        for i, row in enumerate(rows):
            set_table_row(
                self.masters_table,
                i,
                [
                    str(row["id_master"]),
                    str(row["fio"] or ""),
                    str(row["specialization"] or ""),
                    str(row["phone"] or ""),
                    str(row["email"] or ""),
                    str(row["hire_date"] or ""),
                ],
            )

    def _add_master(self) -> None:
        dialog = MasterEditDialog(self, title="Новый мастер")
        if dialog.exec_() != dialog.Accepted:
            return
        data = dialog.get_data()
        self.db.create_master(**data)
        self._refresh_masters()

    def _edit_master(self) -> None:
        id_master = self._selected_id(self.masters_table)
        if id_master is None:
            QMessageBox.information(self, "Инфо", "Выберите мастера")
            return

        current = None
        for row in self.db.list_masters():
            if int(row["id_master"]) == id_master:
                current = row
                break
        if current is None:
            return

        dialog = MasterEditDialog(
            self,
            title="Изменить мастера",
            fio=str(current["fio"] or ""),
            specialization=str(current["specialization"] or ""),
            phone=str(current["phone"] or ""),
            email=str(current["email"] or ""),
            hire_date=str(current["hire_date"] or ""),
            is_active=int(current["is_active"] or 0),
        )
        if dialog.exec_() != dialog.Accepted:
            return
        data = dialog.get_data()
        self.db.update_master(id_master=id_master, **data)
        self._refresh_masters()

    def _refresh_services(self) -> None:
        clear_table(self.services_table)
        rows = self.db.list_services()
        for i, row in enumerate(rows):
            set_table_row(
                self.services_table,
                i,
                [
                    str(row["id_service"]),
                    str(row["category_name"] or ""),
                    str(row["service_name"] or ""),
                    str(row["price"] or ""),
                    str(row["duration_minutes"] or ""),
                ],
            )

    def _add_service(self) -> None:
        dialog = ServiceEditDialog(self, db=self.db, title="Новая услуга")
        if dialog.exec_() != dialog.Accepted:
            return
        data = dialog.get_data()
        self.db.create_service(**data)
        self._refresh_services()

    def _edit_service(self) -> None:
        id_service = self._selected_id(self.services_table)
        if id_service is None:
            QMessageBox.information(self, "Инфо", "Выберите услугу")
            return

        current = None
        for row in self.db.list_services():
            if int(row["id_service"]) == id_service:
                current = row
                break
        if current is None:
            return

        dialog = ServiceEditDialog(
            self,
            db=self.db,
            title="Изменить услугу",
            id_category=int(current["id_category"] or 0),
            service_name=str(current["service_name"] or ""),
            description="",
            price=float(current["price"] or 0),
            duration_minutes=int(current["duration_minutes"] or 0),
            required_materials="",
            is_active=int(current["is_active"] or 0),
        )
        if dialog.exec_() != dialog.Accepted:
            return
        data = dialog.get_data()
        self.db.update_service(id_service=id_service, **data)
        self._refresh_services()

    def _load_appointments(self, date_from: Optional[date], date_to: Optional[date]) -> None:
        clear_table(self.appointments_table)
        rows = self.db.list_appointments(date_from, date_to)
        for i, row in enumerate(rows):
            set_table_row(
                self.appointments_table,
                i,
                [
                    str(row["id_appointment"]),
                    str(row["appointment_date"] or ""),
                    str(row["appointment_time"] or ""),
                    str(row["status"] or ""),
                    str(row["client_fio"] or ""),
                    str(row["master_fio"] or ""),
                    str(row["service_name"] or ""),
                    str(row["total_price"] or ""),
                ],
            )

    def _filter_appointments(self) -> None:
        d_from = self.date_from.date().toPyDate()
        d_to = self.date_to.date().toPyDate()
        if d_from > d_to:
            QMessageBox.warning(self, "Ошибка", "Некорректный период")
            return
        self._load_appointments(d_from, d_to)

    def _show_all_appointments(self) -> None:
        self._load_appointments(None, None)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F5:
            self._refresh_clients()
            self._refresh_masters()
            self._refresh_services()
            self._show_all_appointments()
            return
        super().keyPressEvent(event)