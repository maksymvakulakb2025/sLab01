from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=40)


class CategoryRead(CategoryCreate):
    id: int


class RecordCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    code: str = Field(..., min_length=3, max_length=40)
    title: str = Field(..., min_length=3, max_length=120)
    category_id: int = Field(..., gt=0)
    value: int = Field(..., ge=0, description="Кількість спрацювань")
    status: Literal["new", "in_progress", "done"]


class RecordRead(RecordCreate):
    id: int
    category_name: str


class RecordReplace(RecordCreate):
    pass