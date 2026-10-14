import argparse
import logging
from pathlib import Path

from labs.lab02.task1 import Admin, User, UserAccount
from labs.lab02.task2 import run_availability_scan


def run_demo():
    print("=== ДЕМОНСТРАЦІЯ ЗАВДАННЯ 1 (ООП) ===")

    user = User(username="j_doe", email="john.doe@example.com", role="user")
    user.set_password("SecurePass123!")

    admin = Admin(
        username="sys_admin",
        email="admin.root@example.com",
        permissions=["read", "write", "execute"],
    )
    admin.set_password("RootAdmin2026!")

    account = UserAccount(user=user)

    print("\n1. Перевірка аутентифікації:")
    print("Невдалий вхід:", account.login("j_doe", "WrongPass", "192.168.1.10"))
    print("Статус авторизації:", account.is_authenticated())

    print("Успішний вхід:", account.login("j_doe", "SecurePass123!", "192.168.1.10"))
    print("Статус авторизації:", account.is_authenticated())

    print("\n2. Перевірка валідації email:")
    try:
        user.email = "invalid-email-format"
    except ValueError as e:
        print("Впіймано очікувану помилку:", e)

    print("\n3. Перевірка прав адміністратора:")
    print(admin)
    print("Чи є право 'delete'?:", admin.has_permission("delete"))
    admin.grant_permission("delete")
    print("Після надання 'delete':", admin.has_permission("delete"))

    print("\n4. Журнал аудиту (AuditLog):")
    account.logout()
    for record in account["audit_log"].show_all():
        print(
            f"[{record.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}] {record.username} -> {record.action}"
        )


def main():
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

    parser = argparse.ArgumentParser(description="Лабораторна робота №2 CLI Utility")
    subparsers = parser.add_subparsers(dest="command", help="Доступні команди")

    subparsers.add_parser("demo", help="Запустити демонстрацію Завдання 1")

    analyze_parser = subparsers.add_parser(
        "analyze", help="Запустити сканер доступності сервісів"
    )
    analyze_parser.add_argument(
        "--targets",
        type=Path,
        default=Path("labs/lab02/data/targets.json"),
        help="Шлях до JSON файлу з цілями",
    )
    analyze_parser.add_argument(
        "--timeout",
        type=float,
        default=2.0,
        help="Таймаут підключення в секундах",
    )
    analyze_parser.add_argument(
        "--out-csv",
        type=Path,
        default=Path("labs/lab02/data/scan_results.csv"),
        help="Шлях для вивантаження CSV звіту",
    )
    analyze_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Детальний режим логування",
    )

    args = parser.parse_args()

    if args.command == "demo":
        run_demo()
    elif args.command == "analyze":
        if args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        run_availability_scan(args.targets, args.timeout, args.out_csv, args.verbose)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
