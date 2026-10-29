import sqlite3
from typing import Any


def get_categories(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute("SELECT id, name FROM categories ORDER BY id ASC").fetchall()


def get_category_by_id(conn: sqlite3.Connection, category_id: int) -> sqlite3.Row | None:
    return conn.execute("SELECT id, name FROM categories WHERE id = ?", (category_id,)).fetchone()


def get_category_by_name(conn: sqlite3.Connection, name: str) -> sqlite3.Row | None:
    return conn.execute("SELECT id, name FROM categories WHERE name = ?", (name,)).fetchone()


def create_category(conn: sqlite3.Connection, name: str) -> int:
    cursor = conn.execute("INSERT INTO categories (name) VALUES (?)", (name,))
    return cursor.lastrowid


def delete_category(conn: sqlite3.Connection, category_id: int) -> None:
    conn.execute("DELETE FROM categories WHERE id = ?", (category_id,))


def get_record_by_code(conn: sqlite3.Connection, code: str) -> sqlite3.Row | None:
    return conn.execute("SELECT id FROM records WHERE code = ?", (code,)).fetchone()


def get_record_by_id(conn: sqlite3.Connection, record_id: int) -> sqlite3.Row | None:
    query = """
        SELECT r.id, r.code, r.title, r.category_id, r.value, r.status, c.name as category_name
        FROM records r
        JOIN categories c ON r.category_id = c.id
        WHERE r.id = ?
    """
    return conn.execute(query, (record_id,)).fetchone()


def get_records(
        conn: sqlite3.Connection,
        category_id: int | None = None,
        status: str | None = None,
        min_value: int | None = None,
        q: str | None = None,
        limit: int = 20,
        offset: int = 0
) -> list[sqlite3.Row]:
    query = """
        SELECT r.id, r.code, r.title, r.category_id, r.value, r.status, c.name as category_name
        FROM records r
        JOIN categories c ON r.category_id = c.id
        WHERE 1=1
    """
    params = []

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

    return conn.execute(query, tuple(params)).fetchall()


def create_record(conn: sqlite3.Connection, data: dict[str, Any]) -> int:
    query = """
        INSERT INTO records (code, title, category_id, value, status)
        VALUES (?, ?, ?, ?, ?)
    """
    cursor = conn.execute(query, (
        data["code"], data["title"], data["category_id"], data["value"], data["status"]
    ))
    return cursor.lastrowid


def update_record(conn: sqlite3.Connection, record_id: int, data: dict[str, Any]) -> None:
    query = """
        UPDATE records
        SET code = ?, title = ?, category_id = ?, value = ?, status = ?
        WHERE id = ?
    """
    conn.execute(query, (
        data["code"], data["title"], data["category_id"], data["value"], data["status"], record_id
    ))


def delete_record(conn: sqlite3.Connection, record_id: int) -> None:
    conn.execute("DELETE FROM records WHERE id = ?", (record_id,))