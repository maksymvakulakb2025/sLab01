import os
import random
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from shared.student import STUDENT_NAME, VARIANT_NUMBER

PASSWORDS = [
    "p@ssw0rd5",
    "Admin2026!",
    "12345678",
    "qwertyuiop",
    "SuperSecure!99",
    "pass5",
    "V@riant5_Pass",
    "123456",
    "root_access",
    "CyberSec_2026!",
]
CRITERIA = {
    "min_length": 10,
    "require_digits": True,
    "require_upper": True,
    "require_special": True,
}
FORBIDDEN_PASSWORDS = {"123456", "12345678", "qwertyuiop", "admin", "root_access"}


def evaluate_password(password: str, all_passwords: list) -> str:
    min_len = CRITERIA["min_length"]

    if password in FORBIDDEN_PASSWORDS or len(password) < 6:
        return "Заборонений"

    has_digit = any(c.isdigit() for c in password)
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_special = any(not c.isalnum() for c in password)

    checks = [has_digit, has_upper, has_lower, has_special]
    passed_count = sum(checks)

    if passed_count == 4 and len(password) >= min_len:
        if len(password) >= min_len + 4 and all_passwords.count(password) == 1:
            return "Дуже сильний"
        return "Сильний"
    elif passed_count >= 2 and len(password) >= 8:
        return "Середній"
    return "Слабкий"


def run_task1():
    print(f"\n--- Завдання 1 | Студент: {STUDENT_NAME} (Варіант {VARIANT_NUMBER}) ---")

    working_passwords = PASSWORDS.copy()
    duplicates = random.sample(working_passwords, 3)
    working_passwords.extend(duplicates)

    print(f"{'Пароль':<20} | {'Оцінка надійності'}")
    print("-" * 42)
    for pwd in working_passwords:
        rating = evaluate_password(pwd, working_passwords)
        print(f"{pwd:<20} | {rating}")


if __name__ == "__main__":
    run_task1()
    # by OpenAI чатом джіпітішечкою