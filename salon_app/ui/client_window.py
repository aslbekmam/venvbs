from typing import Optional
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtWidgets import *
from salon_app.db_access import AuthUser, Db
from salon_app.ui.table_helpers import clear_table, set_table_row


class BookingDialog(QDialog):
    def __init__(self, db: Db, *, user: AuthUser):
        super().__init__()
        self.db = db
        self.user = user

        self.service_combo = QComboBox()
        self.master_combo = QComboBox()
        self.additional_combo = QComboBox()

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setDate(QDate.currentDate())

        self.time_input = QLineEdit("10:00:00")

        self.planned_start = QDateEdit()
        self.planned_end = QDateEdit()
        self.planned_start.setCalendarPopup(True)
        self.planned_end.setCalendarPopup(True)
        self.planned_start.setDisplayFormat("yyyy-MM-dd")
        self.planned_end.setDisplayFormat("yyyy-MM-dd")
        self.planned_start.setDate(QDate.currentDate())
        self.planned_end.setDate(QDate.currentDate())

        self._load_lists()
        self.date_edit.dateChanged.connect(self._update_available_masters)

        form = QFormLayout()
        form.addRow("Дата", self.date_edit)
        form.addRow("Время (HH:MM:SS)", self.time_input)
        form.addRow("Услуга", self.service_combo)
        form.addRow("Мастер", self.master_combo)
        form.addRow("Планируемо с", self.planned_start)
        form.addRow("Планируемо по", self.planned_end)

        book_button = QPushButton("Записаться")
        cancel_button = QPushButton("Отмена")
        book_button.clicked.connect(self._book)
        cancel_button.clicked.connect(self.reject)

        actions = QHBoxLayout()
        actions.addStretch(1)
        actions.addWidget(book_button)
        actions.addWidget(cancel_button)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Запись"))
        layout.addLayout(form)
        layout.addLayout(actions)
        self.setLayout(layout)

        self.setWindowTitle("Новая запись")
        self.setMinimumSize(520, 420)

    def _load_lists(self) -> None:
        self.services = self.db.list_active_services()
        self.service_combo.clear()
        self.service_combo.addItems(
            [f"{row['service_name']} ({row['price']})" for row in self.services]
        )

        self._update_available_masters()

    def _update_available_masters(self) -> None:
        appointment_date = self.date_edit.date().toPyDate()
        appointment_time = self.time_input.text().strip()
        masters = self.db.list_available_masters(appointment_date, appointment_time)
        self.masters = masters
        self.master_combo.clear()
        for row in masters:
            self.master_combo.addItem(str(row["fio"]))

    def _selected_service_id(self) -> Optional[int]:
        idx = self.service_combo.currentIndex()
        if idx < 0 or idx >= len(self.services):
            return None
        return int(self.services[idx]["id_service"])

    def _selected_master_id(self) -> Optional[int]:
        idx = self.master_combo.currentIndex()
        if idx < 0 or idx >= len(self.masters):
            return None
        return int(self.masters[idx]["id_master"])

    def _book(self) -> None:
        if self.user.id_client is None:
            QMessageBox.critical(self, "Ошибка", "Для пользователя не привязан клиент")
            return

        id_service = self._selected_service_id()
        id_master = self._selected_master_id()
        if id_service is None or id_master is None:
            QMessageBox.warning(self, "Ошибка", "Выберите услугу и мастера")
            return

        appointment_date = self.date_edit.date().toPyDate()
        appointment_time = self.time_input.text().strip()
        planned_start = self.planned_start.date().toPyDate()
        planned_end = self.planned_end.date().toPyDate()

        ok, status, _id = self.db.create_appointment_with_form(
            id_client=self.user.id_client,
            id_master=id_master,
            id_service=id_service,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            passport_number="",
            visit_purpose="",
            planned_start=planned_start,
            planned_end=planned_end,
            id_additional_option=None,
            additional_notes="",
        )
        if not ok:
            QMessageBox.warning(self, "Статус", status)
            return
        QMessageBox.information(self, "Статус", status)
        self.accept()


class ClientWindow(QWidget):
    def __init__(self, db: Db, user: AuthUser):
        super().__init__()
        self.db = db
        self.user = user

        self.tabs = QTabWidget()

        self.available_tab = self._build_available_tab()
        self.appointments_tab = self._build_appointments_tab()

        self.tabs.addTab(self.available_tab, "Доступно")
        self.tabs.addTab(self.appointments_tab, "Мои записи")

        layout = QVBoxLayout()
        layout.addWidget(self.tabs)
        self.setLayout(layout)

        self.setWindowTitle("Клиент")
        self.setMinimumSize(900, 620)

        self._refresh_my_appointments()

    def _build_available_tab(self) -> QWidget:
        root = QWidget()
        layout = QVBoxLayout(root)

        controls = QHBoxLayout()
        self.period_from = QDateEdit()
        self.period_to = QDateEdit()
        self.period_from.setCalendarPopup(True)
        self.period_to.setCalendarPopup(True)
        self.period_from.setDisplayFormat("yyyy-MM-dd")
        self.period_to.setDisplayFormat("yyyy-MM-dd")
        self.period_from.setDate(QDate.currentDate().addDays(-3))
        self.period_to.setDate(QDate.currentDate().addDays(3))

        search_button = QPushButton("Показать")
        book_button = QPushButton("Записаться")

        search_button.clicked.connect(self._search_available)
        book_button.clicked.connect(self._open_booking)

        controls.addWidget(QLabel("Период"))
        controls.addWidget(self.period_from)
        controls.addWidget(self.period_to)
        controls.addWidget(search_button)
        controls.addStretch(1)
        controls.addWidget(book_button)

        self.available_list = QListWidget()

        layout.addLayout(controls)
        layout.addWidget(self.available_list, 1)
        return root

    def _build_appointments_tab(self) -> QWidget:
        root = QWidget()
        layout = QVBoxLayout(root)

        self.my_table = QTableWidget(0, 6)
        self.my_table.setHorizontalHeaderLabels(["ID", "Дата", "Время", "Статус", "Мастер", "Услуга"])
        self.my_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.my_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.my_table.verticalHeader().setVisible(False)
        self.my_table.horizontalHeader().setStretchLastSection(True)

        layout.addWidget(self.my_table, 1)
        return root

    def _search_available(self) -> None:
        d_from = self.period_from.date().toPyDate()
        d_to = self.period_to.date().toPyDate()
        if d_from > d_to:
            QMessageBox.warning(self, "Ошибка", "Некорректный период")
            return
        self.available_list.clear()
        rows = self.db.list_available_masters_in_period(d_from, d_to)
        if not rows:
            self.available_list.addItem("Нет свободных мастеров на выбранный период")
            return
        for row in rows:
            self.available_list.addItem(f"{row['fio']} (ID {row['id_master']})")

    def _open_booking(self) -> None:
        dialog = BookingDialog(self.db, user=self.user)
        if dialog.exec_() == dialog.Accepted:
            self._refresh_my_appointments()

    def _refresh_my_appointments(self) -> None:
        if self.user.id_client is None:
            return
        clear_table(self.my_table)
        rows = self.db.list_client_appointments(self.user.id_client)
        for i, row in enumerate(rows):
            set_table_row(
                self.my_table,
                i,
                [
                    str(row["id_appointment"]),
                    str(row["appointment_date"] or ""),
                    str(row["appointment_time"] or ""),
                    str(row["status"] or ""),
                    str(row["master_fio"] or ""),
                    str(row["service_name"] or ""),
                ],
            )

    def _selected_appointment_id(self) -> Optional[int]:
        row = self.my_table.currentRow()
        if row < 0:
            return None
        item = self.my_table.item(row, 0)
        if item is None:
            return None
        try:
            return int(item.text())
        except ValueError:
            return None

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F5:
            self._refresh_my_appointments()
            return
        super().keyPressEvent(event)