import csv
import hashlib
import json
import os
import sys
from datetime import datetime, timezone

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from shared.student import VARIANT_NUMBER


class ValidationError(Exception):
    """Кастомний виняток для помилок валідації[cite: 1]."""


def log_event(func):
    """Декоратор логування результатів автентифікації[cite: 1]."""

    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        log_dir = os.path.join(os.path.dirname(__file__), "data")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "log.json")

        log_entry = {
            "event": func.__name__,
            "user": args[0] if args else kwargs.get("username", "unknown"),
            "result": "success" if result else "failure",
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        }

        logs = []
        if os.path.exists(log_file):
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    logs = json.load(f)
            except json.JSONDecodeError:
                logs = []

        logs.append(log_entry)
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=4, ensure_ascii=False)

        return result

    return wrapper


def generate_hash(password: str, salt: str = "00005") -> str:
    """Генерує SHA-256 хеш з сіллю для Варіанту 5[cite: 1]."""
    if not password or not salt:
        raise ValueError("Пароль та сіль не можуть бути порожніми")
    if len(password) < 8:
        raise ValidationError("Пароль коротший за мінімально дозволену довжину")

    data = (password + salt).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def create_users_db():
    salt = f"{VARIANT_NUMBER:05d}"
    users_data = [(f"user_v5_{i}", f"SecurePass5!_{i}") for i in range(1, 11)]

    data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(data_dir, exist_ok=True)
    csv_file = os.path.join(data_dir, "users.csv")

    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["username", "password_hash"])
        for username, pwd in users_data:
            pwd_hash = generate_hash(pwd, salt)
            writer.writerow([username, pwd_hash])


@log_event
def login(username: str, password: str) -> bool:
    if not username or not password:
        raise ValueError("Логін і пароль є обов'язковими")

    salt = f"{VARIANT_NUMBER:05d}"
    csv_file = os.path.join(os.path.dirname(__file__), "data", "users.csv")

    if not os.path.exists(csv_file):
        raise FileNotFoundError("Базу даних users.csv не знайдено")

    target_hash = generate_hash(password, salt)

    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["username"] == username and row["password_hash"] == target_hash:
                return True
    return False


def run_task3():
    print(f"\n--- Завдання 3 | Хешування та логування (Варіант {VARIANT_NUMBER}) ---")
    try:
        create_users_db()
        print("Базу даних користувачів створено у data/users.csv")

        test_user = "user_v5_1"
        test_pass = "SecurePass5!_1"
        res = login(test_user, test_pass)
        print(f"Спроба входу ({test_user}): {'Успішна' if res else 'Невдала'}")

    except (ValueError, ValidationError, FileNotFoundError) as e:
        print(f"Помилка виконання: {e}")


if __name__ == "__main__":
    run_task3()
