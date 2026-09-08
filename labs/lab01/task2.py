import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from shared.student import VARIANT_NUMBER

# Налаштування Варіанту 5[cite: 1]
USERS = {
    "sec_admin": {
        "role": "admin",
        "clearance": 4,
        "department": "Security",
        "active": True,
    },
    "dev_john": {
        "role": "developer",
        "clearance": 3,
        "department": "IT",
        "active": True,
    },
    "auditor_v5": {
        "role": "auditor",
        "clearance": 2,
        "department": "Audit",
        "active": True,
    },
    "intern_m": {"role": "intern", "clearance": 1, "department": "HR", "active": False},
}
RESOURCES = [
    ("financial_report", 3),
    ("system_logs", 2),
    ("classified_core", 4),
    ("public_portal", 1),
]
SECURITY_LEVELS = ("Public", "Internal", "Confidential", "Secret")
BLOCKED_USERS = {"intern_m", "blacklisted_user"}


def check_access(
    username: str, resource_name: str, resource_level: int
) -> tuple[str, str]:
    """Перевіряє доступ за політикою безпеки[cite: 1]."""
    if username not in USERS:
        return "DENY", "User not found"
    if username in BLOCKED_USERS:
        return "DENY", "User is blocked"

    user = USERS[username]
    if not user["active"]:
        return "DENY", "Account inactive"
    if user["clearance"] >= resource_level:
        return "ALLOW", "Access granted"
    return "DENY", "Insufficient clearance"


def run_task2():
    print(f"\n--- Завдання 2 | Контроль доступу (Варіант {VARIANT_NUMBER}) ---")

    print("\n[Список ресурсів]")
    for res_name, level in RESOURCES:
        label = SECURITY_LEVELS[level - 1]
        print(f"- {res_name}: {label} (Рівень {level})")

    print("\n[Перевірка прав доступу]")
    for username in USERS:
        for res_name, level in RESOURCES:
            status, reason = check_access(username, res_name, level)
            print(f"user=[{username}] resource=[{res_name:<16}] -> {status} ({reason})")


if __name__ == "__main__":
    run_task2()
