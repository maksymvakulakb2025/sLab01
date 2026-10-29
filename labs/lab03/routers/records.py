import sqlite3
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, status
from ..database import get_db_connection
from ..schemas import RecordCreate, RecordRead, RecordReplace
from ..repository import (
    get_records, get_record_by_id, create_record,
    update_record, delete_record, get_category_by_id
)

router = APIRouter(prefix="/records", tags=["Records"])


def get_db():
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()


@router.get("", response_model=list[RecordRead])
def read_records(
        category_id: Annotated[int | None, Query(gt=0)] = None,
        status_filter: Annotated[str | None, Query(alias="status")] = None,
        min_value: Annotated[int | None, Query(ge=0)] = None,
        q: str | None = None,
        limit: Annotated[int, Query(ge=1, le=100)] = 20,
        offset: Annotated[int, Query(ge=0)] = 0,
        conn: sqlite3.Connection = Depends(get_db)
):
    rows = get_records(conn, category_id, status_filter, min_value, q, limit, offset)
    return [dict(row) for row in rows]


@router.post("", response_model=RecordRead, status_code=status.HTTP_201_CREATED)
def create_new_record(record: RecordCreate, conn: sqlite3.Connection = Depends(get_db)):
    cat = get_category_by_id(conn, record.category_id)
    if not cat:
        raise HTTPException(status_code=422, detail="Category does not exist")

    try:
        record_id = create_record(conn, record.model_dump())
        conn.commit()
        return dict(get_record_by_id(conn, record_id))
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Record code already exists or validation failed")


@router.get("/{record_id}", response_model=RecordRead)
def read_record(record_id: int, conn: sqlite3.Connection = Depends(get_db)):
    row = get_record_by_id(conn, record_id)
    if not row:
        raise HTTPException(status_code=404, detail="Record not found")
    return dict(row)


@router.put("/{record_id}", response_model=RecordRead)
def update_existing_record(record_id: int, record: RecordReplace, conn: sqlite3.Connection = Depends(get_db)):
    existing = get_record_by_id(conn, record_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Record not found")

    cat = get_category_by_id(conn, record.category_id)
    if not cat:
        raise HTTPException(status_code=422, detail="Category does not exist")

    try:
        update_record(conn, record_id, record.model_dump())
        conn.commit()
        return dict(get_record_by_id(conn, record_id))
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Record code already exists or validation failed")


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_record(record_id: int, conn: sqlite3.Connection = Depends(get_db)):
    existing = get_record_by_id(conn, record_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Record not found")

    delete_record(conn, record_id)
    conn.commit()
    return None
