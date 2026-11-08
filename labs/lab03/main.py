"""FastAPI-застосунок лабораторної роботи №3."""

import logging
import sqlite3
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from labs.lab03.config import DOMAIN_DESCRIPTION, DOMAIN_NAME
from labs.lab03.database import initialize_database
from labs.lab03.repository import ConflictError, NotFoundError
from labs.lab03.routers import categories, records
from labs.lab03.schemas import StudentRead
from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Створити відсутні таблиці під час запуску (дані не змінюються)."""
    initialize_database()
    yield


app = FastAPI(
    title=DOMAIN_NAME,
    description=DOMAIN_DESCRIPTION,
    version="1.0.0",
    lifespan=lifespan,
)
app.include_router(categories.router)
app.include_router(records.router)


@app.exception_handler(NotFoundError)
async def not_found_handler(_: Request, error: NotFoundError) -> JSONResponse:
    """Перетворити NotFoundError на 404."""
    return JSONResponse(status_code=404, content={"detail": str(error)})


@app.exception_handler(ConflictError)
async def conflict_handler(_: Request, error: ConflictError) -> JSONResponse:
    """Перетворити ConflictError на 409."""
    return JSONResponse(status_code=409, content={"detail": str(error)})


@app.exception_handler(sqlite3.Error)
async def sqlite_error_handler(_: Request, error: sqlite3.Error) -> JSONResponse:
    """Записати технічну помилку в лог і повернути загальне повідомлення."""
    logger.error("Помилка SQLite: %s", error, exc_info=error)
    return JSONResponse(
        status_code=500,
        content={"detail": "Внутрішня помилка роботи з базою даних"},
    )


@app.get("/ping", summary="Перевірка доступності API", tags=["service"])
def ping() -> dict[str, str]:
    """Повернути статус ok."""
    return {"status": "ok"}


@app.get(
    "/student",
    response_model=StudentRead,
    summary="Дані студента",
    tags=["service"],
)
def student() -> StudentRead:
    """Повернути ПІБ, групу та номер варіанта з shared/student.py."""
    return StudentRead(
        student_name=STUDENT_NAME,
        group_name=GROUP_NAME,
        variant_number=VARIANT_NUMBER,
    )
