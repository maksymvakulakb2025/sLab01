import sqlite3
from .config import DB_PATH, BASE_DIR


def get_db_connection():
    """Створює та повертає підключення до БД."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    # Щоб звертатися до колонок за іменами, а не індексами
    conn.row_factory = sqlite3.Row

    # Обов'язково вмикаємо підтримку зовнішніх ключів для SQLite
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    """Ініціалізує базу даних на основі schema.sql."""
    # Створюємо директорію для БД, якщо її ще немає
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    schema_path = BASE_DIR / "schema.sql"

    with get_db_connection() as conn:
        with open(schema_path, "r", encoding="utf-8") as f:
            conn.executescript(f.read())
        conn.commit()