from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import Optional

from app.database import db
from app.auth.dependencies import get_current_user
from app.auth.schemas import UserResponse
from app.services.book_service import BookService
from app.schemas.book import BookCreate, BookResponse, BookListResponse
from app.repository.book_repository import BookRepository
from app.core.rate_limiter import rate_limit

router = APIRouter()


def get_book_service() -> BookService:
    repository = BookRepository(db)
    return BookService(repository)


@router.post("/", response_model=BookResponse, status_code=201)
async def create_book(
    request: Request,
    book: BookCreate,
    current_user: UserResponse = Depends(get_current_user),
    service: BookService = Depends(get_book_service),
):
    """Додати нову книгу (потрібна авторизація)"""
    await rate_limit(request, user_id=current_user.id)
    return await service.create_book(book)


@router.get("/", response_model=BookListResponse)
async def get_books(
    request: Request,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[str] = None,
    author: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user),
    service: BookService = Depends(get_book_service),
):
    """Отримати список книг з пагінацією (потрібна авторизація)"""
    await rate_limit(request, user_id=current_user.id)
    books = await service.get_all_books(status=status, author=author, limit=limit, offset=offset)
    total = len(books)
    return BookListResponse(items=books, limit=limit, offset=offset, total=total)


@router.get("/{book_id}", response_model=BookResponse)
async def get_book(
    request: Request,
    book_id: str,
    current_user: UserResponse = Depends(get_current_user),
    service: BookService = Depends(get_book_service),
):
    """Отримати книгу за ID (потрібна авторизація)"""
    await rate_limit(request, user_id=current_user.id)
    book = await service.get_book_by_id(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@router.delete("/{book_id}", status_code=204)
async def delete_book(
    request: Request,
    book_id: str,
    current_user: UserResponse = Depends(get_current_user),
    service: BookService = Depends(get_book_service),
):
    """Видалити книгу (потрібна авторизація)"""
    await rate_limit(request, user_id=current_user.id)
    success = await service.delete_book(book_id)
    if not success:
        raise HTTPException(status_code=404, detail="Book not found")
    return None
