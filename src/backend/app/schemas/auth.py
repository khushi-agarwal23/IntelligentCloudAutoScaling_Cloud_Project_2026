from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class UserRegister(BaseModel):
    email: str = Field(..., min_length=5, max_length=255, description="Valid user email address")
    password: str = Field(..., min_length=6, description="Password with minimum 6 characters")
    full_name: str = Field("", description="Full name of user")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Invalid email format")
        return v


class UserLogin(BaseModel):
    email: str = Field(..., min_length=5, description="Registered email address")
    password: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    exp: Optional[int] = None


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
