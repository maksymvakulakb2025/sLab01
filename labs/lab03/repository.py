"""Параметризовані SQL-запити до бази даних."""

import sqlite3
from contextlib import closing
from typing import Any, NoReturn

from labs.lab03.database import get_connection

Row = dict[str, Any]

RECORD_SELECT = (
    "SELECT r.id, r.code, r.title, r.category_id, "
    "c.name AS category_name, r.value, r.status "
    "FROM records AS r "
    "JOIN categories AS c ON c.id = r.category_id"
)

INSERT_RECORD = (
    "INSERT INTO records (code, title, category_id, value, status) "
    "VALUES (?, ?, ?, ?, ?)"
)


class RepositoryError(Exception):
    """Базова помилка шару доступу до даних."""


class NotFoundError(RepositoryError):
    """Запис або категорію не знайдено."""


class ConflictError(RepositoryError):
    """Порушення унікальності або зв'язків."""


def _connect() -> sqlite3.Connection:
    """Відкрити з'єднання з рядками у вигляді sqlite3.Row."""
    connection = get_connection()
    connection.row_factory = sqlite3.Row
    return connection


def _raise_for_integrity(error: sqlite3.IntegrityError, message: str) -> NoReturn:
    """Перетворити IntegrityError на помилку шару даних."""
    text = str(error)
    if "UNIQUE constraint failed" in text:
        raise ConflictError(message) from error
    if "FOREIGN KEY constraint failed" in text:
        raise NotFoundError("Категорію не знайдено") from error
    raise error


def _ensure_category_exists(connection: sqlite3.Connection, category_id: int) -> None:
    """Перевірити існування категорії."""
    row = connection.execute(
        "SELECT id FROM categories WHERE id = ?", (category_id,)
    ).fetchone()
    if row is None:
        raise NotFoundError("Категорію не знайдено")


def _fetch_record(connection: sqlite3.Connection, record_id: int) -> Row:
    """Отримати запис з назвою категорії або викликати NotFoundError."""
    row = connection.execute(RECORD_SELECT + " WHERE r.id = ?", (record_id,)).fetchone()
    if row is None:
        raise NotFoundError("Запис не знайдено")
    return dict(row)


def _record_params(data: Row) -> tuple[Any, ...]:
    """Зібрати параметри запису у фіксованому порядку."""
    return (
        data["code"],
        data["title"],
        data["category_id"],
        data["value"],
        data["status"],
    )


def _insert_record(connection: sqlite3.Connection, data: Row) -> int:
    """Додати запис і повернути його id."""
    cursor = connection.execute(INSERT_RECORD, _record_params(data))
    if cursor.lastrowid is None:
        raise RepositoryError("Не вдалося отримати id нового запису")
    return cursor.lastrowid


def create_category(name: str) -> Row:
    """Створити категорію."""
    with closing(_connect()) as connection:
        try:
            with connection:
                cursor = connection.execute(
                    "INSERT INTO categories (name) VALUES (?)", (name,)
                )
                category_id = cursor.lastrowid
        except sqlite3.IntegrityError as error:
            _raise_for_integrity(error, "Категорія з такою назвою вже існує")
    return {"id": category_id, "name": name}


def list_categories() -> list[Row]:
    """Отримати всі категорії за зростанням id."""
    with closing(_connect()) as connection:
        rows = connection.execute(
            "SELECT id, name FROM categories ORDER BY id ASC"
        ).fetchall()
    return [dict(row) for row in rows]


def delete_category(category_id: int) -> None:
    """Видалити порожню категорію."""
    with closing(_connect()) as connection:
        try:
            with connection:
                exists = connection.execute(
                    "SELECT id FROM categories WHERE id = ?", (category_id,)
                ).fetchone()
                if exists is None:
                    raise NotFoundError("Категорію не знайдено")
                count = connection.execute(
                    "SELECT COUNT(*) FROM records WHERE category_id = ?",
                    (category_id,),
                ).fetchone()[0]
                if count > 0:
                    raise ConflictError("Категорія містить записи")
                connection.execute(
                    "DELETE FROM categories WHERE id = ?", (category_id,)
                )
        except sqlite3.IntegrityError as error:
            raise ConflictError("Категорія містить записи") from error


def create_record(data: Row) -> Row:
    """Створити запис і повернути його разом з назвою категорії."""
    with closing(_connect()) as connection:
        try:
            with connection:
                _ensure_category_exists(connection, data["category_id"])
                record_id = _insert_record(connection, data)
                result = _fetch_record(connection, record_id)
        except sqlite3.IntegrityError as error:
            _raise_for_integrity(error, "Запис з таким code вже існує")
    return result


def get_record(record_id: int) -> Row:
    """Отримати запис за id."""
    with closing(_connect()) as connection:
        return _fetch_record(connection, record_id)


def list_records(
    *,
    category_id: int | None = None,
    status: str | None = None,
    min_value: int | None = None,
    q: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[Row]:
    """Отримати записи з фільтрами (через AND) і поділом на сторінки."""
    conditions: list[str] = []
    params: list[Any] = []
    if category_id is not None:
        conditions.append("r.category_id = ?")
        params.append(category_id)
    if status is not None:
        conditions.append("r.status = ?")
        params.append(status)
    if min_value is not None:
        conditions.append("r.value >= ?")
        params.append(min_value)
    if q is not None:
        conditions.append("instr(r.title, ?) > 0")
        params.append(q)
    query = RECORD_SELECT
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY r.id ASC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    with closing(_connect()) as connection:
        rows = connection.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def replace_record(record_id: int, data: Row) -> Row:
    """Повністю замінити змінювані поля запису; id не змінюється."""
    with closing(_connect()) as connection:
        try:
            with connection:
                _fetch_record(connection, record_id)
                _ensure_category_exists(connection, data["category_id"])
                connection.execute(
                    "UPDATE records SET code = ?, title = ?, category_id = ?, "
                    "value = ?, status = ? WHERE id = ?",
                    (*_record_params(data), record_id),
                )
                result = _fetch_record(connection, record_id)
        except sqlite3.IntegrityError as error:
            _raise_for_integrity(error, "Запис з таким code вже існує")
    return result


def delete_record(record_id: int) -> None:
    """Видалити запис."""
    with closing(_connect()) as connection, connection:
        _fetch_record(connection, record_id)
        connection.execute("DELETE FROM records WHERE id = ?", (record_id,))


def create_records_bulk(items: list[Row]) -> list[Row]:
    """Атомарно додати пакет записів в одній транзакції."""
    with closing(_connect()) as connection:
        try:
            with connection:
                for category_id in sorted({item["category_id"] for item in items}):
                    _ensure_category_exists(connection, category_id)
                created_ids = [_insert_record(connection, item) for item in items]
                result = [_fetch_record(connection, new_id) for new_id in created_ids]
        except sqlite3.IntegrityError as error:
            _raise_for_integrity(error, "Запис з таким code вже існує")
    return result
