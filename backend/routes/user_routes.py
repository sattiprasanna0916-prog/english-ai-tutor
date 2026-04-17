from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field, EmailStr

from backend.services.user_service import (
    register_user,
    get_user,
    get_user_by_email,
)

from backend.services.auth_service import create_access_token

router = APIRouter(prefix="/users", tags=["Users"])


# -----------------------------
# MODELS
# -----------------------------
class UserRegisterRequest(BaseModel):
    email: EmailStr
    branch: str = Field(..., min_length=1)
    current_level: str = Field(default="Beginner")


class LoginRequest(BaseModel):
    email: EmailStr


# -----------------------------
# REGISTER
# -----------------------------
@router.post("/register")
def register_user_route(payload: UserRegisterRequest):
    user = register_user(
        email=payload.email,
        branch=payload.branch,
        current_level=payload.current_level
    )

    return {
        "user": user
    }


# -----------------------------
# LOGIN (TOKEN GENERATION)
# -----------------------------
@router.post("/login")
def login_user(payload: LoginRequest):
    user = get_user_by_email(payload.email)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # ✅ FIX: use correct key
    user_id = user.get("user_id") or user.get("id")

    if not user_id:
        raise HTTPException(status_code=500, detail="User ID missing")

    token = create_access_token({
        "sub": str(user_id)
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }
# -----------------------------
# GET USER BY EMAIL
# -----------------------------
@router.post("/by-email")
def get_user_by_email_route(email: EmailStr = Body(...)):
    user = get_user_by_email(email)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


# -----------------------------
# GET USER BY ID
# -----------------------------
@router.get("/{user_id}")
def get_user_route(user_id: int):
    user = get_user(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user