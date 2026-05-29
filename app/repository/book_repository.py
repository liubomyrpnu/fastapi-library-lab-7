from typing import List, Optional
from app.models.book import Book, BookCreate
from pydantic_mongo import PydanticObjectId

class BookRepository:
    def __init__(self, db):
        self.collection = db.books

    async def get_all(
        self,
        status: Optional[str] = None,
        author: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List[Book]:
        query = {}
        if status:
            query["status"] = status
        if author:
            query["author"] = {"$regex": author, "$options": "i"}

        cursor = self.collection.find(query).skip(offset).limit(limit)
        books = await cursor.to_list(length=limit)
        return [Book(**book) for book in books]

    async def get_by_id(self, book_id: str) -> Optional[Book]:
        book = await self.collection.find_one({"_id": PydanticObjectId(book_id)})
        return Book(**book) if book else None

    async def create(self, book_create: BookCreate) -> Book:
        book_dict = book_create.model_dump()
        result = await self.collection.insert_one(book_dict)
        book_dict["_id"] = result.inserted_id
        return Book(**book_dict)

    async def delete(self, book_id: str) -> bool:
        result = await self.collection.delete_one({"_id": PydanticObjectId(book_id)})
        return result.deleted_count > 0