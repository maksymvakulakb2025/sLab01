import sqlite3
from fastapi import APIRouter, Depends, HTTPException, status
from ..database import get_db_connection
from ..schemas import CategoryCreate, CategoryRead
from ..repository import get_categories, get_category_by_id, create_category

router = APIRouter(prefix="/categories", tags=["Categories"])

def get_db():
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()

@router.get("", response_model=list[CategoryRead])
def read_categories(conn: sqlite3.Connection = Depends(get_db)):
    return [dict(row) for row in get_categories(conn)]

@router.get("/{category_id}", response_model=CategoryRead)
def read_category(category_id: int, conn: sqlite3.Connection = Depends(get_db)):
    cat = get_category_by_id(conn, category_id)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    return dict(cat)

@router.post("", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_new_category(category: CategoryCreate, conn: sqlite3.Connection = Depends(get_db)):
    try:
        cat_id = create_category(conn, category.name)
        conn.commit()
        return {**category.model_dump(), "id": cat_id}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Category with this name already exists")