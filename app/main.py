from fastapi import FastAPI
from app.api.books import router as books_router
from app.auth.router import router as auth_router
from app.database import db
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.users.create_index("username", unique=True)
    await db.users.create_index("email", unique=True)
    print("Database indexes created")
    yield

app = FastAPI(
    title="Library API - Lab 7 (Rate Limiter + JWT)",
    lifespan=lifespan
)

app.include_router(auth_router)
app.include_router(books_router, prefix="/books")

@app.get("/")
async def root():
    return {"message": "API з JWT автентифікацією та Rate Limiter"}