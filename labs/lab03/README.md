# Лабораторна робота №3 — FastAPI + SQLite (варіант 5)

## Предметна область

**Облік спрацювань засобів захисту.** Сервіс зберігає кількість спрацювань
засобів захисту за навчальні інтервали. Усі дані навчальні.

| Поле | Значення |
|---|---|
| `categories.name` | джерело спрацювання: `firewall`, `ids`, `antivirus` |
| `records.code` | унікальний код запису, наприклад `V05-01` |
| `records.title` | назва запису, наприклад `Підсумок спрацювань 01` |
| `records.value` | кількість подій, ціле число `>= 0` |
| `records.status` | `new`, `in_progress` або `done` |

Одиниця вимірювання: `events`. Поріг: `15`.

## Встановлення

З кореня репозиторію (віртуальне середовище з ЛР №1 активне):

```bash
pip install -r requirements.txt
```

## Запуск

```bash
python -m labs.lab03.database
python -m labs.lab03.seed
uvicorn labs.lab03.main:app --reload --host 127.0.0.1 --port 8000
```

Swagger UI: http://127.0.0.1:8000/docs  
OpenAPI-схема: http://127.0.0.1:8000/openapi.json

Повторний запуск `python -m labs.lab03.seed` не змінює дані та не додає дублікатів.

## Приклади запитів

```bash
curl -i "http://127.0.0.1:8000/ping"
curl -i "http://127.0.0.1:8000/student"
curl -i "http://127.0.0.1:8000/categories"
curl -i "http://127.0.0.1:8000/records?category_id=1&status=new&limit=5&offset=0"

curl -i -X POST "http://127.0.0.1:8000/records" \
  -H "Content-Type: application/json" \
  -d '{"code":"V05-TEST","title":"Навчальний підсумок","category_id":1,"value":7,"status":"new"}'

curl -i -X PUT "http://127.0.0.1:8000/records/9" \
  -H "Content-Type: application/json" \
  -d '{"code":"V05-TEST","title":"Змінений підсумок","category_id":2,"value":12,"status":"done"}'

curl -i -X DELETE "http://127.0.0.1:8000/records/9"
```

Пакет, що має бути скасований повністю (`V05-01` уже є в базі):

```bash
curl -i -X POST "http://127.0.0.1:8000/records/bulk" \
  -H "Content-Type: application/json" \
  -d '[{"code":"V05-ROLLBACK","title":"Перший елемент","category_id":1,"value":4,"status":"new"},{"code":"V05-01","title":"Дублікат коду","category_id":2,"value":5,"status":"new"}]'
```

Очікується `409 Conflict`; запис `V05-ROLLBACK` у базі відсутній.

## Перевірка стилю

```bash
ruff check labs/lab03
ruff format --check labs/lab03
```
