"""Маршрути для записів."""

from typing import Annotated

from fastapi import APIRouter, Body, Path, Query, Response, status

from labs.lab03 import repository
from labs.lab03.schemas import (
    ErrorResponse,
    RecordCreate,
    RecordRead,
    RecordReplace,
    RecordStatus,
)

router = APIRouter(prefix="/records", tags=["records"])

NOT_FOUND = {"model": ErrorResponse, "description": "Запис або категорію не знайдено"}
CONFLICT = {"model": ErrorResponse, "description": "Дублікат code"}

RecordId = Annotated[int, Path(gt=0, description="Ідентифікатор запису")]


@router.get(
    "",
    response_model=list[RecordRead],
    summary="Список записів з фільтрами",
)
def list_records(
    category_id: Annotated[
        int | None, Query(gt=0, description="Лише записи цієї категорії")
    ] = None,
    status_filter: Annotated[
        RecordStatus | None,
        Query(alias="status", description="Лише записи з цим статусом"),
    ] = None,
    min_value: Annotated[
        int | None,
        Query(ge=0, description="value >= min_value"),
    ] = None,
    q: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=120,
            description="Буквальний підрядок у title (з урахуванням регістру)",
        ),
    ] = None,
    limit: Annotated[int, Query(ge=1, le=100, description="Макс. кількість")] = 20,
    offset: Annotated[int, Query(ge=0, description="Скільки пропустити")] = 0,
) -> list[dict]:
    """Повернути записи, відсортовані за id."""
    return repository.list_records(
        category_id=category_id,
        status=status_filter,
        min_value=min_value,
        q=q,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/bulk",
    response_model=list[RecordRead],
    status_code=status.HTTP_201_CREATED,
    summary="Пакетне створення записів (атомарно)",
    responses={404: NOT_FOUND, 409: CONFLICT},
)
def create_records_bulk(
    payload: Annotated[list[RecordCreate], Body(min_length=1, max_length=100)],
) -> list[dict]:
    """Додати від 1 до 100 записів в одній транзакції."""
    return repository.create_records_bulk([item.model_dump() for item in payload])


@router.get(
    "/{record_id}",
    response_model=RecordRead,
    summary="Отримати запис",
    responses={404: NOT_FOUND},
)
def get_record(record_id: RecordId) -> dict:
    """Повернути один запис за id."""
    return repository.get_record(record_id)


@router.post(
    "",
    response_model=RecordRead,
    status_code=status.HTTP_201_CREATED,
    summary="Створити запис",
    responses={404: NOT_FOUND, 409: CONFLICT},
)
def create_record(payload: RecordCreate) -> dict:
    """Створити запис."""
    return repository.create_record(payload.model_dump())


@router.put(
    "/{record_id}",
    response_model=RecordRead,
    summary="Повна заміна запису",
    responses={404: NOT_FOUND, 409: CONFLICT},
)
def replace_record(record_id: RecordId, payload: RecordReplace) -> dict:
    """Повністю замінити змінювані поля запису."""
    return repository.replace_record(record_id, payload.model_dump())


@router.delete(
    "/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалити запис",
    responses={404: NOT_FOUND},
)
def delete_record(record_id: RecordId) -> Response:
    """Видалити запис."""
    repository.delete_record(record_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)