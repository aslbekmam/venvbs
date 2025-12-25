import sqlite3
from dataclasses import dataclass
from datetime import date
from typing import Optional
from db import get_connection

@dataclass(frozen=True)
class AuthUser:
    id_user: int
    username: str
    role: str
    id_client: Optional[int]


class Db:
    def __init__(self) -> None:
        self.connection = get_connection()

    def close(self) -> None:
        self.connection.close()

    def authenticate(self, username: str, password: str) -> Optional[AuthUser]:
        row = self.connection.execute(
            "SELECT id_user, username, role FROM users WHERE username = ? AND password_hash = ?",
            (username, password),
        ).fetchone()
        if row is None:
            return None

        id_client = None
        if row["role"] == "client":
            mapping = self.connection.execute(
                "SELECT id_client FROM user_clients WHERE id_user = ?",
                (row["id_user"],),
            ).fetchone()
            if mapping is not None:
                id_client = int(mapping["id_client"])

        return AuthUser(
            id_user=int(row["id_user"]),
            username=str(row["username"]),
            role=str(row["role"]),
            id_client=id_client,
        )

    def list_clients(self) -> list[sqlite3.Row]:
        return self.connection.execute(
            "SELECT id_client, fio, birth_date, phone, email, registration_date FROM clients ORDER BY id_client"
        ).fetchall()

    def get_client_profile(self, id_client: int) -> Optional[sqlite3.Row]:
        return self.connection.execute(
            """
            SELECT id_client, passport_number, planned_start, planned_end, id_additional_option, additional_notes
            FROM client_profiles
            WHERE id_client = ?
            """,
            (id_client,),
        ).fetchone()

    def upsert_client_profile(
        self,
        *,
        id_client: int,
        passport_number: str,
        planned_start: str,
        planned_end: str,
        id_additional_option: Optional[int],
        additional_notes: str,
    ) -> None:
        self.connection.execute(
            """
            INSERT INTO client_profiles (id_client, passport_number, planned_start, planned_end, id_additional_option, additional_notes)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id_client) DO UPDATE SET
                passport_number = excluded.passport_number,
                planned_start = excluded.planned_start,
                planned_end = excluded.planned_end,
                id_additional_option = excluded.id_additional_option,
                additional_notes = excluded.additional_notes
            """,
            (
                id_client,
                passport_number,
                planned_start,
                planned_end,
                id_additional_option,
                additional_notes,
            ),
        )
        self.connection.commit()

    def create_client(self, fio: str, birth_date: str, phone: str, email: str, registration_date: str) -> None:
        self.connection.execute(
            "INSERT INTO clients (fio, birth_date, phone, email, registration_date) VALUES (?, ?, ?, ?, ?)",
            (fio, birth_date, phone, email, registration_date),
        )
        self.connection.commit()

    def update_client(self, id_client: int, fio: str, birth_date: str, phone: str, email: str, registration_date: str) -> None:
        self.connection.execute(
            "UPDATE clients SET fio = ?, birth_date = ?, phone = ?, email = ?, registration_date = ?, updated_at = CURRENT_TIMESTAMP WHERE id_client = ?",
            (fio, birth_date, phone, email, registration_date, id_client),
        )
        self.connection.commit()

    def list_masters(self) -> list[sqlite3.Row]:
        return self.connection.execute(
            "SELECT id_master, fio, specialization, phone, email, hire_date, is_active FROM masters ORDER BY id_master"
        ).fetchall()

    def create_master(
        self, fio: str, specialization: str, phone: str, email: str, hire_date: str, is_active: int
    ) -> None:
        self.connection.execute(
            "INSERT INTO masters (fio, specialization, phone, email, hire_date, is_active) VALUES (?, ?, ?, ?, ?, ?)",
            (fio, specialization, phone, email, hire_date, is_active),
        )
        self.connection.commit()

    def update_master(
        self, id_master: int, fio: str, specialization: str, phone: str, email: str, hire_date: str, is_active: int
    ) -> None:
        self.connection.execute(
            "UPDATE masters SET fio = ?, specialization = ?, phone = ?, email = ?, hire_date = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP WHERE id_master = ?",
            (fio, specialization, phone, email, hire_date, is_active, id_master),
        )
        self.connection.commit()

    def list_services(self) -> list[sqlite3.Row]:
        return self.connection.execute(
            """
            SELECT s.id_service, s.id_category, c.category_name, s.service_name, s.price, s.duration_minutes, s.is_active
            FROM service_pricelist s
            LEFT JOIN service_categories c ON c.id_category = s.id_category
            ORDER BY s.id_service
            """
        ).fetchall()

    def list_categories(self) -> list[sqlite3.Row]:
        return self.connection.execute(
            "SELECT id_category, category_name FROM service_categories WHERE is_active = 1 ORDER BY category_name"
        ).fetchall()

    def list_active_masters(self) -> list[sqlite3.Row]:
        return self.connection.execute(
            "SELECT id_master, fio FROM masters WHERE is_active = 1 ORDER BY fio"
        ).fetchall()

    def list_active_services(self) -> list[sqlite3.Row]:
        return self.connection.execute(
            "SELECT id_service, service_name, price FROM service_pricelist WHERE is_active = 1 ORDER BY service_name"
        ).fetchall()

    def create_service(
        self,
        id_category: int,
        service_name: str,
        description: str,
        price: float,
        duration_minutes: int,
        required_materials: str,
        is_active: int,
    ) -> None:
        self.connection.execute(
            """
            INSERT INTO service_pricelist (
                id_category, service_name, description, price, duration_minutes, required_materials, is_active
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (id_category, service_name, description, price, duration_minutes, required_materials, is_active),
        )
        self.connection.commit()

    def update_service(
        self,
        id_service: int,
        id_category: int,
        service_name: str,
        description: str,
        price: float,
        duration_minutes: int,
        required_materials: str,
        is_active: int,
    ) -> None:
        self.connection.execute(
            """
            UPDATE service_pricelist
            SET id_category = ?, service_name = ?, description = ?, price = ?, duration_minutes = ?, required_materials = ?,
                is_active = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id_service = ?
            """,
            (id_category, service_name, description, price, duration_minutes, required_materials, is_active, id_service),
        )
        self.connection.commit()

    def list_appointments(
        self, date_from: Optional[date] = None, date_to: Optional[date] = None
    ) -> list[sqlite3.Row]:
        if date_from is None or date_to is None:
            return self.connection.execute(
                """
                SELECT a.id_appointment, a.appointment_date, a.appointment_time, a.status,
                       cl.fio AS client_fio, m.fio AS master_fio, s.service_name, a.total_price
                FROM appointments a
                LEFT JOIN clients cl ON cl.id_client = a.id_client
                LEFT JOIN masters m ON m.id_master = a.id_master
                LEFT JOIN service_pricelist s ON s.id_service = a.id_service
                ORDER BY a.appointment_date DESC, a.appointment_time DESC
                """
            ).fetchall()

        return self.connection.execute(
            """
            SELECT a.id_appointment, a.appointment_date, a.appointment_time, a.status,
                   cl.fio AS client_fio, m.fio AS master_fio, s.service_name, a.total_price
            FROM appointments a
            LEFT JOIN clients cl ON cl.id_client = a.id_client
            LEFT JOIN masters m ON m.id_master = a.id_master
            LEFT JOIN service_pricelist s ON s.id_service = a.id_service
            WHERE a.appointment_date BETWEEN ? AND ?
            ORDER BY a.appointment_date DESC, a.appointment_time DESC
            """,
            (date_from.isoformat(), date_to.isoformat()),
        ).fetchall()

    def list_client_appointments(self, id_client: int) -> list[sqlite3.Row]:
        return self.connection.execute(
            """
            SELECT a.id_appointment, a.appointment_date, a.appointment_time, a.status,
                   m.fio AS master_fio, s.service_name, a.total_price
            FROM appointments a
            LEFT JOIN masters m ON m.id_master = a.id_master
            LEFT JOIN service_pricelist s ON s.id_service = a.id_service
            WHERE a.id_client = ?
            ORDER BY a.appointment_date DESC, a.appointment_time DESC
            """,
            (id_client,),
        ).fetchall()

    def is_master_available(self, id_master: int, appointment_date: date, appointment_time: str) -> bool:
        row = self.connection.execute(
            """
            SELECT 1 FROM appointments
            WHERE id_master = ? AND appointment_date = ? AND appointment_time = ?
              AND status IN ('Запланирован', 'Клиент пришёл', 'Выполняется')
            LIMIT 1
            """,
            (id_master, appointment_date.isoformat(), appointment_time),
        ).fetchone()
        return row is None

    def list_available_masters(self, appointment_date: date, appointment_time: str) -> list[sqlite3.Row]:
        return self.connection.execute(
            """
            SELECT m.id_master, m.fio
            FROM masters m
            WHERE m.is_active = 1
              AND NOT EXISTS (
                SELECT 1
                FROM appointments a
                WHERE a.id_master = m.id_master
                  AND a.appointment_date = ?
                  AND a.appointment_time = ?
                  AND a.status IN ('Запланирован', 'Клиент пришёл', 'Выполняется')
              )
            ORDER BY m.fio
            """,
            (appointment_date.isoformat(), appointment_time),
        ).fetchall()

    def list_available_masters_in_period(self, date_from: date, date_to: date) -> list[sqlite3.Row]:
        return self.connection.execute(
            """
            SELECT m.id_master, m.fio
            FROM masters m
            WHERE m.is_active = 1
              AND NOT EXISTS (
                SELECT 1
                FROM appointments a
                WHERE a.id_master = m.id_master
                  AND a.appointment_date BETWEEN ? AND ?
                  AND a.status IN ('Запланирован', 'Клиент пришёл', 'Выполняется')
              )
            ORDER BY m.fio
            """,
            (date_from.isoformat(), date_to.isoformat()),
        ).fetchall()

    def create_appointment_with_form(
        self,
        *,
        id_client: int,
        id_master: int,
        id_service: int,
        appointment_date: date,
        appointment_time: str,
        passport_number: str,
        visit_purpose: str,
        planned_start: date,
        planned_end: date,
        id_additional_option: Optional[int],
        additional_notes: str,
    ) -> tuple[bool, str, Optional[int]]:
        if planned_start > planned_end:
            return False, "Некорректный период", None

        if not self.is_master_available(id_master, appointment_date, appointment_time):
            return False, "Мастер занят на выбранные дату/время", None

        cursor = self.connection.execute(
            """
            INSERT INTO appointments (
                id_client, id_master, id_service, appointment_date, appointment_time, status, total_price, notes
            )
            VALUES (?, ?, ?, ?, ?, 'Запланирован',
                    (SELECT price FROM service_pricelist WHERE id_service = ?),
                    ?)
            """,
            (
                id_client,
                id_master,
                id_service,
                appointment_date.isoformat(),
                appointment_time,
                id_service,
                additional_notes,
            ),
        )
        id_appointment = int(cursor.lastrowid)

        self.connection.execute(
            """
            INSERT INTO appointment_forms (
                id_appointment, passport_number, visit_purpose, planned_start, planned_end, id_additional_option
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                id_appointment,
                passport_number,
                visit_purpose,
                planned_start.isoformat(),
                planned_end.isoformat(),
                id_additional_option,
            ),
        )

        self.connection.execute(
            """
            INSERT INTO client_profiles (id_client, passport_number, planned_start, planned_end, id_additional_option, additional_notes)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id_client) DO UPDATE SET
                passport_number = excluded.passport_number,
                planned_start = excluded.planned_start,
                planned_end = excluded.planned_end,
                id_additional_option = excluded.id_additional_option,
                additional_notes = excluded.additional_notes
            """,
            (
                id_client,
                passport_number,
                planned_start.isoformat(),
                planned_end.isoformat(),
                id_additional_option,
                additional_notes,
            ),
        )

        self.connection.commit()
        return True, "Запись создана", id_appointment

    def list_additional_options(self) -> list[sqlite3.Row]:
        return self.connection.execute(
            "SELECT id_option, option_name FROM additional_info_options ORDER BY option_name"
        ).fetchall()