from typing import List, Optional
from app.repository.book_repository import BookRepository
from app.models.book import BookCreate, Book

class BookService:
    def __init__(self, repository: BookRepository):
        self.repository = repository

    async def get_all_books(
        self,
        status: Optional[str] = None,
        author: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List[Book]:
        return await self.repository.get_all(status, author, limit, offset)

    async def get_book_by_id(self, book_id: str) -> Optional[Book]:
        return await self.repository.get_by_id(book_id)

    async def create_book(self, book_create: BookCreate) -> Book:
        return await self.repository.create(book_create)

    async def delete_book(self, book_id: str) -> bool:
        return await self.repository.delete(book_id)