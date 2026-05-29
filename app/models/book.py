from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from enum import Enum
from pydantic_mongo import PydanticObjectId

class BookStatus(str, Enum):
    AVAILABLE = "available"
    ISSUED = "issued"

class BookBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    author: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    status: BookStatus
    year: int = Field(..., ge=1000, le=2100)

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

class BookCreate(BookBase):
    pass

class Book(BookBase):
    id: Optional[PydanticObjectId] = Field(None, alias="_id")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={PydanticObjectId: str}
    )