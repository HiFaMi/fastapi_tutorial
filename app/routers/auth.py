from datetime import datetime, timedelta

import bcrypt
import jwt
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from app.database.conn import db
from app.common.consts import JWT_SECRET, JWT_ALGORITHM
from app.database.schema import Users
from app.models import SnsType, Token, UserRegister, UserToken

router = APIRouter()


@router.post("/auth/register/{sns_type}", status_code=200, response_model=Token)
async def register_user(sns_type: SnsType, register_info: UserRegister, session: Session = Depends(db.session)):
    """
    회원가입 API
    :param sns_type:
    :param register_info:
    :param session:
    :return:
    """
    if sns_type == SnsType.email:
        is_exists = await is_email_exists(register_info.email)
        if not register_info.email or not register_info.pw:
            return JSONResponse(status_code=400, content=dict(msg="email and pw must be provided"))

        elif is_exists:
            return JSONResponse(status_code=400, content=dict(msg="email already registered"))

        # hash는 byte만 가능
        hashed_pw = bcrypt.hashpw(register_info.pw.encode("utf-8"), bcrypt.gensalt())
        new_user = Users.create(
            session,
            auto_commit=True,
            email=register_info.email,
            pw=hashed_pw.decode("utf-8"),
        )
        token = dict(Authorization=f"Bearer {create_access_token(data=UserToken.from_orm(new_user).dict(exclude={'pw', 'marketing_agree'}),)}")
        return token

    return JSONResponse(status_code=400, content=dict(msg="Not Supported"))


@router.post("/auth/login/{sns_type}", response_model=Token)
async def login(sns_type: SnsType, user_info: UserRegister):
    if sns_type == SnsType.email:
        is_exists = await is_email_exists(user_info.email)
        if not user_info.email or not user_info.pw:
            return JSONResponse(status_code=400, content=dict(msg="email and pw must be provided"))
        elif not is_exists:
            return JSONResponse(status_code=400, content=dict(msg="no match user"))

        user = Users.get(email=user_info.email)
        is_verified = bcrypt.checkpw(user_info.pw.encode("utf-8"), user.pw.encode("utf-8"))

        if not is_verified:
            return JSONResponse(status_code=400, content=dict(msg="no match user"))

        token = dict(Authorization=f"Bearer {create_access_token(data=UserToken.from_orm(user).dict(exclude={'pw', 'marketing_agree'}),)}")
        return token
    return JSONResponse(status_code=400, content=dict(msg="Not Supported"))


async def is_email_exists(email: str) -> bool:
    get_email = Users.get(email=email)
    if get_email:
        return True
    return False


def create_access_token(data: dict = None, expires_delta: int = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        to_encode.update({"exp": datetime.utcnow() + timedelta(hours=expires_delta)})

    encode_jwt = jwt.encode(to_encode, JWT_SECRET, JWT_ALGORITHM)
    return encode_jwt
