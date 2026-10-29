import json
import sqlite3
from .config import SEED_FILE
from .database import get_db_connection
from .repository import create_category, create_record, get_category_by_name, get_record_by_code


def seed_data():
    """Заповнює базу даних початковими даними з seed.json."""
    if not SEED_FILE.exists():
        print(f"Файл {SEED_FILE} не знайдено. Пропуск наповнення бази.")
        return

    with open(SEED_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    with get_db_connection() as conn:
        # Додаємо категорії
        for cat in data.get("categories", []):
            try:
                # Перевіряємо чи немає вже такої категорії, щоб не було дублікатів
                if not get_category_by_name(conn, cat["name"]):
                    create_category(conn, cat["name"])
            except sqlite3.IntegrityError:
                pass

        # Додаємо записи
        for rec in data.get("records", []):
            try:
                if not get_record_by_code(conn, rec["code"]):
                    create_record(conn, rec)
            except sqlite3.IntegrityError:
                pass

        conn.commit()
