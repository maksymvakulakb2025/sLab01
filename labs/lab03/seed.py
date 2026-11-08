"""Скрипт ініціалізації та початкового заповнення (seed) бази даних."""

import json

from labs.lab03 import database, repository
from labs.lab03.config import SEED_JSON_PATH


def seed_data() -> None:
    """Ідемпотентне заповнення бази тестовими даними з seed.json."""
    database.initialize_database()

    if not SEED_JSON_PATH.exists():
        print(f"[WARNING] Файл seed.json не знайдено: {SEED_JSON_PATH}")
        return

    with open(SEED_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Заповнення категорій
    existing_cats = repository.list_categories()
    existing_cat_names = {c["name"] for c in existing_cats}

    for cat in data.get("categories", []):
        if cat["name"] not in existing_cat_names:
            repository.create_category(cat["name"])
            existing_cat_names.add(cat["name"])

    # 2. Оновлюємо актуальну карту категорій (name -> id)
    current_cats = repository.list_categories()
    cat_map = {c["name"]: c["id"] for c in current_cats}

    # 3. Заповнення записів
    existing_records = repository.list_records(limit=100)
    existing_codes = {r["code"] for r in existing_records}

    for rec in data.get("records", []):
        if rec["code"] not in existing_codes:
            # Отримуємо category_id (за ім'ям або прямим ID)
            cat_id = rec.get("category_id")
            if not cat_id and "category_name" in rec:
                cat_id = cat_map.get(rec["category_name"])

            if cat_id:
                repository.create_record(
                    {
                        "code": rec["code"],
                        "title": rec["title"],
                        "category_id": cat_id,
                        "value": rec["value"],
                        "status": rec["status"],
                    }
                )
                existing_codes.add(rec["code"])

    print("[INFO] Базу даних успішно ініціалізовано та заповнено тестовими даними.")


if __name__ == "__main__":
    seed_data()
