from contextlib import asynccontextmanager
from fastapi import FastAPI

from .database import init_db
from .seed import seed_data
from .config import STUDENT_NAME, GROUP, VARIANT
from .routers import categories, records

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Цей код виконується при запуску сервера
    init_db()
    seed_data()
    yield
    # Тут можна додати код для коректного закриття з'єднань при зупинці сервера

app = FastAPI(
    title="Lab 3 API: Облік спрацювань засобів захисту",
    description=f"Лабораторна робота №3. Виконав: {STUDENT_NAME}, група {GROUP}, Варіант {VARIANT}",
    version="1.0.0",
    lifespan=lifespan
)

# Підключаємо наші роутери з тегами для красивої документації
app.include_router(categories.router)
app.include_router(records.router)

@app.get("/ping", tags=["System"])
def ping():
    """Перевірка статусу сервера."""
    return {"status": "ok", "message": "Server is running"}

@app.get("/student", tags=["System"])
def get_student_info():
    """Інформація про виконавця."""
    return {
        "student": STUDENT_NAME,
        "group": GROUP,
        "variant": VARIANT
    }