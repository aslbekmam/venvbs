import sqlite3
from pathlib import Path
from typing import Optional

DB_FILENAME = "beauty_salon.sqlite3"
DB_PATH = Path(__file__).resolve().parent / DB_FILENAME


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    connection = sqlite3.connect(str(db_path or DB_PATH))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _create_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS clients (
            id_client INTEGER PRIMARY KEY AUTOINCREMENT,
            fio TEXT,
            birth_date DATE,
            phone TEXT,
            email TEXT,
            registration_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS additional_info_options (
            id_option INTEGER PRIMARY KEY AUTOINCREMENT,
            option_name TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS client_profiles (
            id_client INTEGER PRIMARY KEY,
            passport_number TEXT,
            planned_start DATE,
            planned_end DATE,
            id_additional_option INTEGER,
            additional_notes TEXT,
            FOREIGN KEY (id_client) REFERENCES clients(id_client),
            FOREIGN KEY (id_additional_option) REFERENCES additional_info_options(id_option)
        );

        CREATE TABLE IF NOT EXISTS users (
            id_user INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('admin', 'client')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS user_clients (
            id_user INTEGER PRIMARY KEY,
            id_client INTEGER NOT NULL,
            FOREIGN KEY (id_user) REFERENCES users(id_user),
            FOREIGN KEY (id_client) REFERENCES clients(id_client)
        );

        CREATE TABLE IF NOT EXISTS masters (
            id_master INTEGER PRIMARY KEY AUTOINCREMENT,
            fio TEXT,
            specialization TEXT,
            phone TEXT,
            email TEXT,
            hire_date DATE,
            is_active INTEGER CHECK (is_active IN (0, 1)),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS service_categories (
            id_category INTEGER PRIMARY KEY AUTOINCREMENT,
            category_name TEXT,
            description TEXT,
            is_active INTEGER CHECK (is_active IN (0, 1)),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS service_pricelist (
            id_service INTEGER PRIMARY KEY AUTOINCREMENT,
            id_category INTEGER,
            service_name TEXT,
            description TEXT,
            price NUMERIC,
            duration_minutes INTEGER,
            required_materials TEXT,
            is_active INTEGER CHECK (is_active IN (0, 1)),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (id_category) REFERENCES service_categories(id_category)
        );

        CREATE TABLE IF NOT EXISTS master_schedule (
            id_schedule INTEGER PRIMARY KEY AUTOINCREMENT,
            id_master INTEGER,
            weekday TEXT CHECK (weekday IN (
                'Понедельник',
                'Вторник',
                'Среда',
                'Четверг',
                'Пятница',
                'Суббота',
                'Воскресенье'
            )),
            start_time TIME,
            end_time TIME,
            slot_duration_minutes INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (id_master) REFERENCES masters(id_master)
        );

        CREATE TABLE IF NOT EXISTS appointments (
            id_appointment INTEGER PRIMARY KEY AUTOINCREMENT,
            id_client INTEGER,
            id_master INTEGER,
            id_service INTEGER,
            appointment_date DATE,
            appointment_time TIME,
            status TEXT CHECK (status IN (
                'Запланирован',
                'Клиент пришёл',
                'Выполняется',
                'Завершён',
                'Не явился',
                'Отменён'
            )),
            total_price NUMERIC,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (id_client) REFERENCES clients(id_client),
            FOREIGN KEY (id_master) REFERENCES masters(id_master),
            FOREIGN KEY (id_service) REFERENCES service_pricelist(id_service)
        );

        CREATE TABLE IF NOT EXISTS appointment_forms (
            id_appointment INTEGER PRIMARY KEY,
            passport_number TEXT,
            visit_purpose TEXT,
            planned_start DATE,
            planned_end DATE,
            id_additional_option INTEGER,
            FOREIGN KEY (id_appointment) REFERENCES appointments(id_appointment),
            FOREIGN KEY (id_additional_option) REFERENCES additional_info_options(id_option)
        );

        CREATE TABLE IF NOT EXISTS payments (
            id_payment INTEGER PRIMARY KEY AUTOINCREMENT,
            id_appointment INTEGER,
            payment_date DATE,
            amount NUMERIC,
            payment_method TEXT CHECK (payment_method IN ('Наличные', 'Карта', 'Сертификат', 'Смешанная')),
            FOREIGN KEY (id_appointment) REFERENCES appointments(id_appointment)
        );

        CREATE TABLE IF NOT EXISTS gift_certificates (
            id_certificate INTEGER PRIMARY KEY AUTOINCREMENT,
            id_client INTEGER,
            certificate_number TEXT,
            nominal_value NUMERIC,
            remaining_balance NUMERIC,
            issue_date DATE,
            expiration_date DATE,
            purchaser_name TEXT,
            recipient_name TEXT,
            status TEXT CHECK (status IN ('Активирован', 'Использован', 'Истёк')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (id_client) REFERENCES clients(id_client)
        );
        """
    )


def _table_has_rows(connection: sqlite3.Connection, table_name: str) -> bool:
    cursor = connection.execute(f"SELECT 1 FROM {table_name} LIMIT 1")
    return cursor.fetchone() is not None


def _ensure_column(connection: sqlite3.Connection, table_name: str, column_name: str, column_ddl: str) -> None:
    rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    existing = {row["name"] for row in rows}
    if column_name in existing:
        return
    connection.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_ddl}")


def seed_data(connection: sqlite3.Connection) -> None:
    if not _table_has_rows(connection, "clients"):
        connection.executescript(
            """
            INSERT INTO clients (id_client, fio, birth_date, phone, email, registration_date, created_at, updated_at)
            VALUES
                (1, 'Иванова Анна Петровна', '1990-05-15', '79150001122', 'ivanova@mail.ru', '2023-01-12', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
                (2, 'Петрова Мария Сергеевна', '1985-08-22', '79160004567', 'petrova@mail.ru', '2023-03-08', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
                (3, 'Сидоров Алексей Иванович', '1980-11-30', '79170007890', 'sidorov@mail.ru', '2024-02-15', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
            """
        )

    if not _table_has_rows(connection, "masters"):
        connection.executescript(
            """
            INSERT INTO masters (id_master, fio, specialization, phone, email, hire_date, is_active, created_at, updated_at)
            VALUES
                (1, 'Кузнецова Елена Петровна', 'Парикмахер', '79151112233', 'kuznetsova@salon.ru', '2020-04-01', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
                (2, 'Смирнов Дмитрий Сергеевич', 'Визажист', '79153334455', 'smirnov@salon.ru', '2021-06-15', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
                (3, 'Попова Ольга Ивановна', 'Маникюр', '79156667788', 'popova@salon.ru', '2022-09-10', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
            """
        )

    if not _table_has_rows(connection, "service_categories"):
        connection.executescript(
            """
            INSERT INTO service_categories (id_category, category_name, description, is_active, created_at, updated_at)
            VALUES
                (1, 'Уход за волосами', 'Стрижки, укладки, окрашивание', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
                (2, 'Уход за лицом', 'Чистка лица, маски, массаж', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
                (3, 'Уход за ногтями', 'Маникюр, педикюр, наращивание', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
            """
        )

    if not _table_has_rows(connection, "service_pricelist"):
        connection.executescript(
            """
            INSERT INTO service_pricelist (
                id_service, id_category, service_name, description, price, duration_minutes, required_materials, is_active, created_at, updated_at
            )
            VALUES
                (1, 1, 'Стрижка', 'Моделирующая стрижка', 1500, 60, 'Ножницы, расчёска', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
                (2, 2, 'Чистка лица', 'Глубокая чистка лица', 2000, 90, 'Кремы, маски', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
                (3, 3, 'Маникюр', 'Классический маникюр', 1000, 45, 'Пилки, лаки', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
            """
        )

    if not _table_has_rows(connection, "master_schedule"):
        connection.executescript(
            """
            INSERT INTO master_schedule (
                id_schedule, id_master, weekday, start_time, end_time, slot_duration_minutes, created_at, updated_at
            )
            VALUES
                (1, 1, 'Понедельник', '09:00:00', '18:00:00', 60, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
                (2, 2, 'Вторник', '10:00:00', '19:00:00', 60, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
                (3, 3, 'Среда', '11:00:00', '20:00:00', 60, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
            """
        )

    if not _table_has_rows(connection, "appointments"):
        connection.executescript(
            """
            INSERT INTO appointments (
                id_appointment, id_client, id_master, id_service, appointment_date, appointment_time, status, total_price, notes, created_at, updated_at
            )
            VALUES
                (1, 1, 1, 1, '2024-03-01', '10:00:00', 'Завершён', 1500, 'Стрижка', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
                (2, 2, 2, 2, '2024-03-02', '11:00:00', 'Запланирован', 2000, 'Чистка лица', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
                (3, 3, 3, 3, '2024-03-03', '12:00:00', 'Завершён', 1000, 'Маникюр', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
            """
        )

    if not _table_has_rows(connection, "payments"):
        connection.executescript(
            """
            INSERT INTO payments (id_payment, id_appointment, payment_date, amount, payment_method)
            VALUES
                (1, 1, '2024-03-01', 1500, 'Карта'),
                (2, 2, '2024-03-02', 2000, 'Наличные'),
                (3, 3, '2024-03-03', 1000, 'Сертификат');
            """
        )

    if not _table_has_rows(connection, "gift_certificates"):
        connection.executescript(
            """
            INSERT INTO gift_certificates (
                id_certificate, id_client, certificate_number, nominal_value, remaining_balance, issue_date, expiration_date,
                purchaser_name, recipient_name, status, created_at, updated_at)
            VALUES
                (1, 1, 'CERT001', 3000, 3000, '2023-12-01', '2024-12-01', 'Иванов Иван Иванович', 'Иванова Анна Петровна', 'Активирован', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
                (2, 2, 'CERT002', 5000, 5000, '2023-11-15', '2024-11-15', 'Петров Сергей Олегович', 'Петрова Мария Сергеевна', 'Активирован', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
                (3, 3, 'CERT003', 2000, 2000, '2024-01-10', '2025-01-10', 'Сидоров Алексей Иванович', 'Сидорова Ольга Ивановна', 'Активирован', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
            """
        )

    if not _table_has_rows(connection, "additional_info_options"):
        connection.executescript(
            """
            INSERT INTO additional_info_options (id_option, option_name)
            VALUES
                (1, 'Аллергии'),
                (2, 'Особые пожелания'),
                (3, 'Требуется консультация');
            """
        )

    if not _table_has_rows(connection, "users"):
        connection.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            ("admin", "admin", "admin"),
        )
        connection.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            ("client", "client", "client"),
        )

    if not _table_has_rows(connection, "user_clients"):
        row = connection.execute("SELECT id_user FROM users WHERE username = ?", ("client",)).fetchone()
        if row is not None:
            connection.execute(
                "INSERT INTO user_clients (id_user, id_client) VALUES (?, ?)",
                (int(row["id_user"]), 1),
            )

    if not _table_has_rows(connection, "client_profiles"):
        connection.execute(
            "INSERT INTO client_profiles (id_client, passport_number, planned_start, planned_end, id_additional_option, additional_notes) VALUES (?, ?, ?, ?, ?, ?)",
            (1, "0000 000000", "2024-03-01", "2024-03-03", 2, ""),)

def init_db(seed: bool = True, db_path: Optional[Path] = None) -> Path:
    connection = get_connection(db_path)
    try:
        _create_schema(connection)
        _ensure_column(connection, "client_profiles", "planned_start", "DATE")
        _ensure_column(connection, "client_profiles", "planned_end", "DATE")
        if seed:
            seed_data(connection)

        connection.execute(
            """
            UPDATE users
            SET password_hash = CASE username
                WHEN 'admin' THEN 'admin'
                WHEN 'client' THEN 'client'
                ELSE password_hash
            END
            WHERE username IN ('admin', 'client')
              AND length(password_hash) = 64
            """)
        connection.commit()
    finally:
        connection.close()
    return db_path or DB_PATH

if __name__ == "__main__":
    init_db(seed=True)