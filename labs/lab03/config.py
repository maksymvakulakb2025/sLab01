"""Налаштування предметної області та обмежень варіанта 5."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "data" / "lab3.sqlite3"
SCHEMA_PATH = BASE_DIR / "schema.sql"
SEED_JSON_PATH = BASE_DIR / "data" / "seed.json"

VARIANT_NUMBER = 5
DOMAIN_NAME = "Облік спрацювань засобів захисту"
DOMAIN_DESCRIPTION = (
    "Сервіс збереження кількості спрацювань засобів захисту за навчальні інтервали. "
    "Категорія визначає джерело спрацювання, value — кількість подій "
    "(одиниця: events, ціле число >= 0), status — стан перевірки підсумкового запису."
)
UNIT = "events"
THRESHOLD = 15
VALUE_MIN = 0
VALUE_MAX = None
