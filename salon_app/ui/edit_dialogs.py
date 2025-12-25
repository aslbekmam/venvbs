from PyQt5.QtWidgets import *
from salon_app.db_access import Db


class ClientEditDialog(QDialog):
    def __init__(
        self,
        parent,
        *,
        title: str,
        fio: str = "",
        birth_date: str = "",
        phone: str = "",
        email: str = "",
        registration_date: str = "",
    ):
        super().__init__(parent)
        self.fio_input = QLineEdit(fio)
        self.birth_date_input = QLineEdit(birth_date)
        self.phone_input = QLineEdit(phone)
        self.email_input = QLineEdit(email)
        self.registration_date_input = QLineEdit(registration_date)

        form = QFormLayout()
        form.addRow("ФИО", self.fio_input)
        form.addRow("Дата рождения (YYYY-MM-DD)", self.birth_date_input)
        form.addRow("Телефон", self.phone_input)
        form.addRow("Email", self.email_input)
        form.addRow("Регистрация (YYYY-MM-DD)", self.registration_date_input)

        save_button = QPushButton("Сохранить")
        cancel_button = QPushButton("Отмена")
        save_button.clicked.connect(self._save)
        cancel_button.clicked.connect(self.reject)

        actions = QHBoxLayout()
        actions.addStretch(1)
        actions.addWidget(save_button)
        actions.addWidget(cancel_button)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addLayout(actions)
        self.setLayout(layout)

        self.setWindowTitle(title)
        self.setMinimumSize(460, 220)

    def _save(self) -> None:
        if not self.fio_input.text().strip():
            QMessageBox.warning(self, "Ошибка", "ФИО обязательно")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "fio": self.fio_input.text().strip(),
            "birth_date": self.birth_date_input.text().strip(),
            "phone": self.phone_input.text().strip(),
            "email": self.email_input.text().strip(),
            "registration_date": self.registration_date_input.text().strip(),
        }


class MasterEditDialog(QDialog):
    def __init__(
        self,
        parent,
        *,
        title: str,
        fio: str = "",
        specialization: str = "",
        phone: str = "",
        email: str = "",
        hire_date: str = "",
        is_active: int = 1,
    ):
        super().__init__(parent)
        self.fio_input = QLineEdit(fio)
        self.specialization_input = QLineEdit(specialization)
        self.phone_input = QLineEdit(phone)
        self.email_input = QLineEdit(email)
        self.hire_date_input = QLineEdit(hire_date)
        form = QFormLayout()
        form.addRow("ФИО", self.fio_input)
        form.addRow("Специализация", self.specialization_input)
        form.addRow("Телефон", self.phone_input)
        form.addRow("Email", self.email_input)
        form.addRow("Дата найма (YYYY-MM-DD)", self.hire_date_input)

        save_button = QPushButton("Сохранить")
        cancel_button = QPushButton("Отмена")
        save_button.clicked.connect(self._save)
        cancel_button.clicked.connect(self.reject)

        actions = QHBoxLayout()
        actions.addStretch(1)
        actions.addWidget(save_button)
        actions.addWidget(cancel_button)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addLayout(actions)
        self.setLayout(layout)

        self.setWindowTitle(title)
        self.setMinimumSize(460, 240)

    def _save(self) -> None:
        if not self.fio_input.text().strip():
            QMessageBox.warning(self, "Ошибка", "ФИО обязательно")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "fio": self.fio_input.text().strip(),
            "specialization": self.specialization_input.text().strip(),
            "phone": self.phone_input.text().strip(),
            "email": self.email_input.text().strip(),
            "hire_date": self.hire_date_input.text().strip(),
            "is_active": 1,
        }


class ServiceEditDialog(QDialog):
    def __init__(
        self,
        parent,
        *,
        db: Db,
        title: str,
        id_category: int = 0,
        service_name: str = "",
        description: str = "",
        price: float = 0.0,
        duration_minutes: int = 30,
        required_materials: str = "",
        is_active: int = 1,
    ):
        super().__init__(parent)
        self.db = db

        self.category_combo = QComboBox()
        categories = self.db.list_categories()
        self.category_ids = [int(row["id_category"]) for row in categories]
        self.category_combo.addItems([str(row["category_name"]) for row in categories])
        if id_category in self.category_ids:
            self.category_combo.setCurrentIndex(self.category_ids.index(id_category))

        self.service_name_input = QLineEdit(service_name)
        self.description_input = QLineEdit(description)
        self.price_input = QLineEdit(str(price))
        self.duration_input = QSpinBox()
        self.duration_input.setMinimum(1)
        self.duration_input.setMaximum(600)
        self.duration_input.setValue(int(duration_minutes))
        self.required_materials_input = QLineEdit(required_materials)

        form = QFormLayout()
        form.addRow("Категория", self.category_combo)
        form.addRow("Название", self.service_name_input)
        form.addRow("Описание", self.description_input)
        form.addRow("Цена", self.price_input)
        form.addRow("Длительность (мин)", self.duration_input)
        form.addRow("Материалы", self.required_materials_input)

        save_button = QPushButton("Сохранить")
        cancel_button = QPushButton("Отмена")
        save_button.clicked.connect(self._save)
        cancel_button.clicked.connect(self.reject)

        actions = QHBoxLayout()
        actions.addStretch(1)
        actions.addWidget(save_button)
        actions.addWidget(cancel_button)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addLayout(actions)
        self.setLayout(layout)

        self.setWindowTitle(title)
        self.setMinimumSize(520, 320)

    def _save(self) -> None:
        if not self.service_name_input.text().strip():
            QMessageBox.warning(self, "Ошибка", "Название услуги обязательно")
            return
        try:
            float(self.price_input.text().strip())
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Некорректная цена")
            return
        self.accept()

    def get_data(self) -> dict:
        index = self.category_combo.currentIndex()
        id_category = self.category_ids[index] if 0 <= index < len(self.category_ids) else 0
        return {
            "id_category": int(id_category),
            "service_name": self.service_name_input.text().strip(),
            "description": self.description_input.text().strip(),
            "price": float(self.price_input.text().strip()),
            "duration_minutes": int(self.duration_input.value()),
            "required_materials": self.required_materials_input.text().strip(),
            "is_active": 1,
        }