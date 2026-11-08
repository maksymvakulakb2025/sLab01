"""Шар доступу до даних (Repository) через SQL-запити."""

import sqlite3
from typing import Any

from labs.lab03.database import get_connection


class RepositoryError(Exception):
    """Базова помилка репозиторію."""


class NotFoundError(RepositoryError):
    """Об'єкт не знайдено (404)."""


class ConflictError(RepositoryError):
    """Конфлікт унікальності або зв'язків (409)."""


def list_categories() -> list[dict[str, Any]]:
    """Отримати всі категорії за зростанням id."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, name FROM categories ORDER BY id ASC"
        ).fetchall()
        return [{"id": row[0], "name": row[1]} for row in rows]


def create_category(name: str) -> dict[str, Any]:
    """Створити нову категорію."""
    with get_connection() as conn:
        try:
            cursor = conn.execute("INSERT INTO categories (name) VALUES (?)", (name,))
            conn.commit()
            return {"id": cursor.lastrowid, "name": name}
        except sqlite3.IntegrityError as err:
            raise ConflictError(f"Категорія з назвою '{name}' вже існує.") from err


def delete_category(category_id: int) -> None:
    """Видалити категорію, якщо вона порожня."""
    with get_connection() as conn:
        # Перевірка чи існує
        cat = conn.execute(
            "SELECT id FROM categories WHERE id = ?", (category_id,)
        ).fetchone()
        if not cat:
            raise NotFoundError(f"Категорію з id={category_id} не знайдено.")

        # Перевірка чи є записи
        rec = conn.execute(
            "SELECT id FROM records WHERE category_id = ? LIMIT 1", (category_id,)
        ).fetchone()
        if rec:
            raise ConflictError(
                f"Неможливо видалити категорію id={category_id}, оскільки вона містить записи."
            )

        conn.execute("DELETE FROM categories WHERE id = ?", (category_id,))
        conn.commit()


def list_records(
    category_id: int | None = None,
    status: str | None = None,
    min_value: int | None = None,
    q: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """Отримати список записів із фільтрацією та пагінацією."""
    query = """
        SELECT r.id, r.code, r.title, r.category_id, r.value, r.status, c.name AS category_name
        FROM records r
        JOIN categories c ON r.category_id = c.id
        WHERE 1=1
    """
    params: list[Any] = []

    if category_id is not None:
        query += " AND r.category_id = ?"
        params.append(category_id)
    if status is not None:
        query += " AND r.status = ?"
        params.append(status)
    if min_value is not None:
        query += " AND r.value >= ?"
        params.append(min_value)
    if q is not None:
        query += " AND instr(r.title, ?) > 0"
        params.append(q)

    query += " ORDER BY r.id ASC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with get_connection() as conn:
        rows = conn.execute(query, tuple(params)).fetchall()
        return [
            {
                "id": r[0],
                "code": r[1],
                "title": r[2],
                "category_id": r[3],
                "value": r[4],
                "status": r[5],
                "category_name": r[6],
            }
            for r in rows
        ]


def get_record(record_id: int) -> dict[str, Any]:
    """Отримати один запис за id."""
    query = """
        SELECT r.id, r.code, r.title, r.category_id, r.value, r.status, c.name AS category_name
        FROM records r
        JOIN categories c ON r.category_id = c.id
        WHERE r.id = ?
    """
    with get_connection() as conn:
        row = conn.execute(query, (record_id,)).fetchone()
        if not row:
            raise NotFoundError(f"Запис з id={record_id} не знайдено.")
        return {
            "id": row[0],
            "code": row[1],
            "title": row[2],
            "category_id": row[3],
            "value": row[4],
            "status": row[5],
            "category_name": row[6],
        }


def create_record(data: dict[str, Any]) -> dict[str, Any]:
    """Створити один запис."""
    with get_connection() as conn:
        try:
            cursor = conn.execute(
                """
                INSERT INTO records (code, title, category_id, value, status)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    data["code"],
                    data["title"],
                    data["category_id"],
                    data["value"],
                    data["status"],
                ),
            )
            record_id = cursor.lastrowid
            conn.commit()
        except sqlite3.IntegrityError as err:
            err_msg = str(err)
            if "FOREIGN KEY" in err_msg.upper():
                raise NotFoundError(
                    f"Категорію з id={data['category_id']} не знайдено."
                ) from err
            raise ConflictError(f"Запис із кодом '{data['code']}' вже існує.") from err

    return get_record(record_id)


def create_records_bulk(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Пакетне створення записів в одній транзакції."""
    created_ids = []
    with get_connection() as conn:
        try:
            for data in items:
                cursor = conn.execute(
                    """
                    INSERT INTO records (code, title, category_id, value, status)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        data["code"],
                        data["title"],
                        data["category_id"],
                        data["value"],
                        data["status"],
                    ),
                )
                created_ids.append(cursor.lastrowid)
            conn.commit()
        except sqlite3.IntegrityError as err:
            conn.rollback()
            err_msg = str(err)
            if "FOREIGN KEY" in err_msg.upper():
                raise NotFoundError(
                    "Категорію для одного з записів не знайдено."
                ) from err
            raise ConflictError(
                "Конфлікт унікальності коду (code) при пакетному додаванні."
            ) from err

    return [get_record(rid) for rid in created_ids]


def replace_record(record_id: int, data: dict[str, Any]) -> dict[str, Any]:
    """Повна заміна запису."""
    with get_connection() as conn:
        # Перевірка чи існує
        existing = conn.execute(
            "SELECT id FROM records WHERE id = ?", (record_id,)
        ).fetchone()
        if not existing:
            raise NotFoundError(f"Запис з id={record_id} не знайдено.")

        try:
            conn.execute(
                """
                UPDATE records
                SET code = ?, title = ?, category_id = ?, value = ?, status = ?
                WHERE id = ?
                """,
                (
                    data["code"],
                    data["title"],
                    data["category_id"],
                    data["value"],
                    data["status"],
                    record_id,
                ),
            )
            conn.commit()
        except sqlite3.IntegrityError as err:
            err_msg = str(err)
            if "FOREIGN KEY" in err_msg.upper():
                raise NotFoundError(
                    f"Категорію з id={data['category_id']} не знайдено."
                ) from err
            raise ConflictError(f"Запис із кодом '{data['code']}' вже існує.") from err

    return get_record(record_id)


def delete_record(record_id: int) -> None:
    """Видалити запис."""
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT id FROM records WHERE id = ?", (record_id,)
        ).fetchone()
        if not existing:
            raise NotFoundError(f"Запис з id={record_id} не знайдено.")

        conn.execute("DELETE FROM records WHERE id = ?", (record_id,))
        conn.commit()
