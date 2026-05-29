from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from app.auth.schemas import UserCreate, Token, TokenRefresh, UserResponse
from app.core.security import get_password_hash, verify_password, create_access_token, create_refresh_token, decode_token
from app.database import db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate):
    existing_user = await db.users.find_one({"username": user.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed_password = get_password_hash(user.password)
    user_dict = user.model_dump()
    user_dict["hashed_password"] = hashed_password
    del user_dict["password"]
    user_dict["role"] = "user"
    user_dict["is_active"] = True

    result = await db.users.insert_one(user_dict)
    user_dict["id"] = str(result.inserted_id)
    return UserResponse(**user_dict)


# OAuth2PasswordRequestForm приймає form-data — саме це очікує Swagger Authorize
@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await db.users.find_one({"username": form_data.username})
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    access_token = create_access_token(data={"sub": str(user["_id"])})
    refresh_token = create_refresh_token(data={"sub": str(user["_id"])})

    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=Token)
async def refresh_token(refresh: TokenRefresh):
    payload = decode_token(refresh.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = payload.get("sub")
    access_token = create_access_token(data={"sub": user_id})

    return Token(access_token=access_token, refresh_token=refresh.refresh_token)
