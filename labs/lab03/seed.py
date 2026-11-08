"""Початкове заповнення бази з data/seed.json."""

import json
import logging
import sqlite3
import sys
from contextlib import closing
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from labs.lab03.database import get_connection, initialize_database
from labs.lab03.schemas import CategoryCreate, RecordCreate

SEED_PATH = Path(__file__).resolve().parent / "data" / "seed.json"
EXPECTED_CATEGORIES = 3
EXPECTED_RECORDS = 8

logger = logging.getLogger(__name__)


class SeedError(Exception):
    """Некоректні початкові дані."""


def load_seed(path: Path = SEED_PATH) -> dict[str, Any]:
    """Прочитати JSON з початковими даними."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise SeedError(f"Файл {path.name} не знайдено") from error
    except json.JSONDecodeError as error:
        raise SeedError(f"Файл {path.name} містить некоректний JSON") from error
    if (
        not isinstance(raw, dict)
        or not isinstance(raw.get("categories"), list)
        or not isinstance(raw.get("records"), list)
    ):
        raise SeedError("JSON має містити масиви categories і records")
    return raw


def validate_seed(
    raw: dict[str, Any],
) -> tuple[list[tuple[int, str]], list[RecordCreate]]:
    """Перевірити початкові дані та повернути категорії й записи."""
    categories: list[tuple[int, str]] = []
    for item in raw["categories"]:
        if not isinstance(item, dict) or set(item) != {"id", "name"}:
            raise SeedError("Категорія має містити лише поля id та name")
        category_id = item["id"]
        if type(category_id) is not int or category_id <= 0:
            raise SeedError("id категорії має бути додатним цілим числом")
        try:
            model = CategoryCreate.model_validate({"name": item["name"]})
        except ValidationError as error:
            raise SeedError(f"Некоректна категорія {item!r}") from error
        categories.append((category_id, model.name))

    category_ids = {category_id for category_id, _ in categories}
    records: list[RecordCreate] = []
    for item in raw["records"]:
        try:
            record = RecordCreate.model_validate(item)
        except ValidationError as error:
            raise SeedError(f"Некоректний запис {item!r}") from error
        if record.category_id not in category_ids:
            raise SeedError(f"Запис {record.code} посилається на невідому категорію")
        records.append(record)

    if len(categories) != EXPECTED_CATEGORIES or len(records) != EXPECTED_RECORDS:
        raise SeedError("Потрібно рівно 3 категорії та 8 записів")
    return categories, records


def is_database_empty() -> bool:
    """Перевірити, що в базі немає категорій і записів."""
    with closing(get_connection()) as connection:
        categories = connection.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
        records = connection.execute("SELECT COUNT(*) FROM records").fetchone()[0]
    return categories == 0 and records == 0


def insert_seed(categories: list[tuple[int, str]], records: list[RecordCreate]) -> None:
    """Додати категорії та записи в одній транзакції."""
    with closing(get_connection()) as connection, connection:
        connection.executemany(
            "INSERT INTO categories (id, name) VALUES (?, ?)", categories
        )
        connection.executemany(
            "INSERT INTO records (code, title, category_id, value, status) "
            "VALUES (?, ?, ?, ?, ?)",
            [
                (item.code, item.title, item.category_id, item.value, item.status)
                for item in records
            ],
        )


def main() -> int:
    """Виконати початкове заповнення; повернути код завершення."""
    try:
        categories, records = validate_seed(load_seed())
        initialize_database()
        if not is_database_empty():
            print("База вже містить дані. Заповнення пропущено, дані не змінено.")
            return 0
        insert_seed(categories, records)
    except SeedError as error:
        print(f"Помилка початкових даних: {error}")
        return 1
    except sqlite3.Error as error:
        logger.error("Помилка SQLite під час заповнення: %s", error, exc_info=error)
        print("Помилка бази даних. Усі зміни скасовано.")
        return 1
    print(f"Додано категорій: {len(categories)}, записів: {len(records)}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
