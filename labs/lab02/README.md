# Лабораторна робота №2. Розробка консольних утиліт для задач кібербезпеки

**Варіант 5:** Сканер доступності мережевих сервісів та перевірка портів.

## Встановлення залежностей

Усі команди виконуються з **кореня репозиторію** `cybersecurity-python-labs`.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

## Структура файлів

```text
labs/lab02/
├── __init__.py
├── main.py        # команди demo та analyze
├── task1.py       # User, Admin, Session, AuditLog, UserAccount
├── task2.py       # сканер доступності сервісів (варіант 5)
├── README.md
└── data/
    ├── data_v05/
    │   └── targets.json   # вхідний список цілей (з lab2_data.zip)
    └── scan_results.csv   # результат сканування (створюється утилітою)
```

Якщо `targets.json` лежить прямо в `data/`, утиліта також знайде його там
(спочатку шукається `data/data_v05/targets.json`, потім `data/targets.json`).

## Вхідні дані

`targets.json` - список об'єктів з полями `host`, `port` та необов'язковим `service`
(також підтримується CSV з такими ж колонками):

```json
[
  {"host": "192.168.1.1", "port": 80, "service": "HTTP"},
  {"host": "example.com", "port": 443, "service": "HTTPS"}
]
```

## Запуск

Завдання 1 (демонстрація ООП):

```bash
python -m labs.lab02.main demo
```

Завдання 2 (сканер):

```bash
python -m labs.lab02.main analyze --targets labs/lab02/data/data_v05/targets.json --timeout 2 --out-csv labs/lab02/data/scan_results.csv --verbose
```

## Параметри команди `analyze`

| Параметр | Тип | За замовчуванням | Опис |
|---|---|---|---|
| `--targets` | шлях | `labs/lab02/data/data_v05/targets.json` (або `data/targets.json`) | файл зі списком цілей |
| `--timeout` | число (с), > 0 | `2.0` | таймаут підключення до одного порту |
| `--out-csv` | шлях | `labs/lab02/data/scan_results.csv` | куди зберегти CSV-звіт |
| `--verbose` | прапорець | вимкнено | детальне логування (рівень DEBUG) |

## Поведінка при помилках

| Ситуація | Результат |
|---|---|
| Файл цілей не знайдено / немає прав | помилка в лог, код завершення `1` |
| Некоректний JSON, порожній список цілей | помилка в лог, код завершення `1` |
| Запис без `host`/`port` або порт не число | запис пропускається, помилка в лог, скан триває |
| Невалідне ім'я хоста або порт поза 1-65535 | статус `INVALID`, скан триває |
| Таймаут з'єднання | статус `OFFLINE`, час відповіді `TIMEOUT` |
| Відмова з'єднання, невідоме ім'я хоста, інша мережева помилка | статус `OFFLINE`, причина в колонці `Notes` |
| `--timeout` не число | помилка `argparse`, код `2` |
| `--timeout` <= 0 | помилка в лог, код `2` |
| Помилка запису CSV | помилка в лог, програма не падає |

Рівні логування: `INFO` - хід роботи, `WARNING` - недоступні вузли,
`ERROR` - некоректні дані, `DEBUG` (з `--verbose`) - доступні вузли.

## Перевірка коду

```bash
ruff check .
ruff format --check .
```