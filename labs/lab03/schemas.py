"""Pydantic-моделі запитів і відповідей."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

RecordStatus = Literal["new", "in_progress", "done"]

# Варіант 5: value — кількість подій, ціле число не менше 0.
Value = Annotated[int, Field(strict=True, ge=0)]


class ErrorResponse(BaseModel):
    """Повідомлення про помилку."""

    detail: str


class CategoryCreate(BaseModel):
    """Дані для створення категорії."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(min_length=2, max_length=40)


class CategoryRead(BaseModel):
    """Категорія у відповіді."""

    id: int
    name: str


class RecordCreate(BaseModel):
    """Дані для створення запису (без id)."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    code: str = Field(min_length=3, max_length=40)
    title: str = Field(min_length=3, max_length=120)
    category_id: int = Field(gt=0)
    value: Value
    status: RecordStatus


class RecordReplace(RecordCreate):
    """Дані для повної заміни запису (усі поля обов'язкові)."""


class RecordRead(RecordCreate):
    """Запис у відповіді."""

    id: int
    category_name: str


class StudentRead(BaseModel):
    """Дані студента."""

    student_name: str
    group_name: str
    variant_number: int
