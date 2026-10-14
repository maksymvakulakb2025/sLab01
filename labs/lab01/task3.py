import csv
import hashlib
import json
import os
import sys
from datetime import datetime, timezone

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from shared.student import VARIANT_NUMBER

SALT = f"{VARIANT_NUMBER:05d}"
MIN_PASSWORD_LENGTH = 16


class ValidationError(Exception):
    """Кастомний виняток для помилок валідації[cite: 1]."""


def log_event(func):
    """Декоратор логування результатів автентифікації[cite: 1]."""

    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        log_dir = os.path.join(os.path.dirname(__file__), "data")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "log.json")

        username = args[0] if args else kwargs.get("username", "unknown")

        log_entry = {
            "event": func.__name__,
            "user": username,
            "result": "success" if result else "failure",
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            "args": list(args),
            "kwargs": kwargs,
        }

        logs = []
        try:
            if os.path.exists(log_file):
                try:
                    with open(log_file, "r", encoding="utf-8") as f:
                        logs = json.load(f)
                except json.JSONDecodeError:
                    logs = []

            logs.append(log_entry)
            with open(log_file, "w", encoding="utf-8") as f:
                json.dump(logs, f, indent=4, ensure_ascii=False)
        except (OSError, FileNotFoundError, PermissionError) as e:
            print(f"Помилка файлової системи при логуванні: {e}")

        return result

    return wrapper


def generate_hash(password: str, salt: str = SALT) -> str:
    """Генерує SHA3-256 хеш з сіллю для Варіанту 5[cite: 1]."""
    if not password or not salt:
        raise ValueError("Пароль та сіль не можуть бути порожніми")
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(
            f"Пароль коротший за мінімально дозволену довжину ({MIN_PASSWORD_LENGTH} символів)"
        )

    data = (password + salt).encode("utf-8")
    return hashlib.sha3_256(data).hexdigest()


users_to_register = tuple(
    (f"user_v5_{i}", f"SecurePass5!_LongSecret_{i}") for i in range(1, 11)
)


def create_user(username: str, password: str) -> tuple:
    """Створює кортеж (username, hash_value) для одного користувача[cite: 1]."""
    pwd_hash = generate_hash(password, SALT)
    return (username, pwd_hash)


def create_users(users_list: tuple | list):
    """Створює CSV-базу даних користувачів із хешами їхніх паролів[cite: 1]."""
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(data_dir, exist_ok=True)
    csv_file = os.path.join(data_dir, "users.csv")

    try:
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["username", "password_hash"])
            for username, pwd in users_list:
                user_entry = create_user(username, pwd)
                writer.writerow(user_entry)
    except (OSError, FileNotFoundError, PermissionError) as e:
        print(f"Помилка при збереженні бази користувачів у файл: {e}")
        raise


def read_users_db() -> list:
    """Зчитує вміст CSV-файлу у список users_db[cite: 1]."""
    csv_file = os.path.join(os.path.dirname(__file__), "data", "users.csv")
    if not os.path.exists(csv_file):
        raise FileNotFoundError("Базу даних users.csv не знайдено")

    users_db = []
    try:
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            users_db.extend(list(reader))
    except (OSError, FileNotFoundError, PermissionError) as e:
        print(f"Помилка при зчитуванні бази користувачів з файлу: {e}")
        raise

    return users_db


def print_users_db(users_db: list):
    """Виводить базу даних у вигляді структурованої таблиці[cite: 1]."""
    print("\n" + "=" * 88)
    print(f"{'Username':<18} | {'Password Hash (SHA3-256)':<65}")
    print("=" * 88)
    for row in users_db:
        print(f"{row['username']:<18} | {row['password_hash']:<65}")
    print("=" * 88 + "\n")


@log_event
def login(username: str, password: str) -> bool:
    """Здійснює перевірку автентифікації користувача[cite: 1]."""
    if not username or not password:
        raise ValueError("Логін і пароль є обов'язковими")

    users_db = read_users_db()
    target_hash = generate_hash(password, SALT)

    for row in users_db:
        if row["username"] == username and row["password_hash"] == target_hash:
            return True
    return False


def main():
    """Головна функція запуску[cite: 1]."""
    print(f"\n--- Завдання 3 | Хешування та логування (Варіант {VARIANT_NUMBER}) ---")
    try:
        # 1. Реєстрація користувачів та створення бази даних
        create_users(users_to_register)
        print("Базу даних користувачів створено у data/users.csv")

        # 2. Читання бази даних та виведення в таблицю
        users_db = read_users_db()
        print_users_db(users_db)

        # 3. Перевірка автентифікації
        test_user = "user_v5_1"
        test_pass = "SecurePass5!_LongSecret_1"
        res = login(test_user, test_pass)
        print(f"Спроба входу ({test_user}): {'Успішна' if res else 'Невдала'}")

        # Тест неправильного пароля
        bad_res = login(test_user, "WrongPassword123456789")
        print(f"Спроба входу з невірним паролем: {'Успішна' if bad_res else 'Невдала'}")

    except (ValidationError, ValueError, FileNotFoundError) as e:
        print(f"Помилка виконання: {e}")


if __name__ == "__main__":
    main()
