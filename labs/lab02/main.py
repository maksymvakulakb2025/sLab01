"""Точка входу ЛР №2: команди demo (Завдання 1) та analyze (Завдання 2)."""

import argparse
import logging
import sys
from datetime import timedelta
from pathlib import Path

from labs.lab02.task1 import SESSION_TIMEOUT_SEC, Admin, User, UserAccount
from labs.lab02.task2 import ScanInputError, run_availability_scan

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent / "data"


def default_targets_path() -> Path:
    """Шукає targets.json у data/data_v05/, а потім у data/."""
    for candidate in (
        DATA_DIR / "data_v05" / "targets.json",
        DATA_DIR / "targets.json",
    ):
        if candidate.exists():
            return candidate
    return DATA_DIR / "data_v05" / "targets.json"


def run_demo() -> None:
    print("=== ДЕМОНСТРАЦІЯ ЗАВДАННЯ 1 (ООП) ===")

    user = User(username="j_doe", email="john_doe@example.com", role="user")
    user.set_password("SecurePass123!")
    admin = Admin(
        username="sys_admin",
        email="admin_root@example.com",
        permissions=["read", "write", "execute"],
    )
    admin.set_password("RootAdmin2026!")
    account = UserAccount(user=user)
    print(user)

    print("\n1. Вхід:")
    print("Невдалий вхід (хибний пароль):", account.login("j_doe", "Wrong", "10.0.0.5"))
    print("Автентифіковано:", account.is_authenticated())
    print("Успішний вхід:", account.login("j_doe", "SecurePass123!", "10.0.0.5"))
    print("Автентифіковано:", account.is_authenticated())

    print("\n2. Зміна email із валідацією:")
    user.email = "new_mail@example.com"
    print("Email змінено на:", user.email)
    for bad in ("invalid-email-format", "a.b@example.com", "ab@example.com"):
        try:
            user.email = bad
        except ValueError as e:
            print("Відхилено:", e)

    print("\n3. Права адміністратора:")
    print(admin)
    print("Чи є право 'delete'?", admin.has_permission("delete"))
    admin.grant_permission("delete")
    print("Після grant 'delete':", admin.has_permission("delete"))
    admin.revoke_permission("write")
    print(admin)

    print("\n4. Захист доступу через ключі:")
    try:
        account["password_hash"]
    except KeyError as e:
        print("KeyError:", e)
    try:
        account["user"] = "not a user"
    except TypeError as e:
        print("TypeError:", e)

    print("\n5. Завершення сеансу за таймаутом:")
    print("Автентифіковано:", account.is_authenticated())
    account.session.last_activity -= timedelta(seconds=SESSION_TIMEOUT_SEC + 1)
    print(
        f"Після {SESSION_TIMEOUT_SEC + 1} с неактивності:", account.is_authenticated()
    )

    print("\n6. Вихід із системи:")
    account.login("j_doe", "SecurePass123!", "10.0.0.5")
    account.logout()
    print("Автентифіковано після logout:", account.is_authenticated())

    print("\n7. Журнал аудиту (AuditLog):")
    for rec in account["audit_log"].show_all():
        stamp = rec.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
        print(f"[{stamp}] {rec.username} -> {rec.action}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Лабораторна робота №2")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("demo", help="Демонстрація Завдання 1 (ООП)")

    analyze = sub.add_parser("analyze", help="Сканер доступності сервісів (варіант 5)")
    analyze.add_argument(
        "--targets",
        type=Path,
        default=default_targets_path(),
        help="JSON/CSV-файл із цілями (host, port, service)",
    )
    analyze.add_argument(
        "--timeout",
        type=float,
        default=2.0,
        help="таймаут з'єднання, секунди (за замовчуванням 2.0)",
    )
    analyze.add_argument(
        "--out-csv",
        type=Path,
        default=DATA_DIR / "scan_results.csv",
        help="шлях до CSV-звіту",
    )
    analyze.add_argument(
        "--verbose", action="store_true", help="детальне логування (DEBUG)"
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    logging.basicConfig(
        level=logging.DEBUG if getattr(args, "verbose", False) else logging.INFO,
        format="[%(levelname)s] %(message)s",
    )

    if args.command == "demo":
        run_demo()
        return 0

    if args.timeout <= 0:
        logger.error("--timeout must be positive")
        return 2
    try:
        run_availability_scan(args.targets, args.timeout, args.out_csv)
    except ScanInputError as e:
        logger.error("%s", e)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())