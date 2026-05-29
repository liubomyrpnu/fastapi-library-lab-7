from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from pydantic_mongo import PydanticObjectId
from enum import Enum

class BookStatus(str, Enum):
    AVAILABLE = "available"
    ISSUED = "issued"

class BookBase(BaseModel):
    title: str
    author: str
    description: Optional[str] = None
    status: BookStatus = BookStatus.AVAILABLE
    year: int

class BookCreate(BookBase):
    pass

class BookResponse(BookBase):
    id: PydanticObjectId = Field(alias="_id")
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        populate_by_name = True

class BookListResponse(BaseModel):
    items: List[BookResponse]
    limit: int
    offset: int
    total: int