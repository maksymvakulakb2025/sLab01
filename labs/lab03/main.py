"""Головний файл FastAPI-додатку."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from labs.lab03 import config, database, repository
from labs.lab03.routers import categories, records
from labs.lab03.schemas import StudentRead


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Ініціалізація бази даних при запуску додатку."""
    database.initialize_database()
    yield


app = FastAPI(
    title=f"Lab 3 - {config.DOMAIN_NAME}",
    description=config.DOMAIN_DESCRIPTION,
    version="1.0.0",
    lifespan=lifespan,
)

# Підключаємо наші маршрути
app.include_router(categories.router)
app.include_router(records.router)


@app.exception_handler(repository.NotFoundError)
async def not_found_handler(request: Request, exc: repository.NotFoundError) -> JSONResponse:
    """Обробка помилки 'Не знайдено' (404)."""
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(repository.ConflictError)
async def conflict_handler(request: Request, exc: repository.ConflictError) -> JSONResponse:
    """Обробка помилки 'Конфлікт унікальності або зв'язків' (409)."""
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.get(
    "/student",
    response_model=StudentRead,
    summary="Дані студента",
    tags=["student"],
)
def get_student() -> dict:
    """Повернути інформацію про автора роботи."""
    return {
        "student_name": "Вакула Максим",
        "group_name": "КБ-207",
        "variant_number": 5,
    }