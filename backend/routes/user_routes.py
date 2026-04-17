from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field, EmailStr

from backend.services.user_service import (
    register_user,
    get_user,
    get_user_by_email,
)

router = APIRouter(prefix="/users", tags=["Users"])


# -----------------------------
# Request Model
# -----------------------------
class UserRegisterRequest(BaseModel):
    email: EmailStr
    branch: str = Field(..., min_length=1)
    current_level: str = Field(default="Beginner")


# -----------------------------
# REGISTER (or return existing)
# -----------------------------
@router.post("/register")
def register_user_route(payload: UserRegisterRequest):
    user = register_user(
        email=payload.email,
        branch=payload.branch,
        current_level=payload.current_level
    )
    return user


# -----------------------------
# LOGIN (BETTER THAN URL EMAIL)
# -----------------------------
from backend.services.auth_service import create_access_token

@router.post("/login")
def login_user(email: EmailStr = Body(...)):
    user = get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    token = create_access_token({"user_id": user["user_id"]})

    return {
        "access_token": token,
        "user": user
    }


# -----------------------------
# GET USER BY EMAIL (OPTIONAL)
# -----------------------------
@router.get("/by-email/{email}")
def get_user_by_email_route(email: str):
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