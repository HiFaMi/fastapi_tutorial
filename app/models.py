# fastapi model은 validation 용도
from pydantic import EmailStr, BaseModel
from enum import Enum


class UserRegister(BaseModel):
    email: EmailStr = None
    pw: str = None


class SnsType(str, Enum):
    email: str = "email"
    facebook: str = "facebook"
    google: str = "google"
    kakao: str = "kakao"


# 아래 response model
class Token(BaseModel):
    Authorization: str = None


class UserToken(BaseModel):
    id: int
    email: str = None
    pw: str = None
    name: str | None = None
    phone_number: str | None = None

    class Config:
        from_attributes = True


class UserMe(BaseModel):
    email: str = None
    name: str | None = None
    phone_number: str | None = None

    class Config:
        from_attributes = True
