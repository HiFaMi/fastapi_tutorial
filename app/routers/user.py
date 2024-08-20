import secrets
import string
from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette.requests import Request

from app.common.consts import MAX_API_KEY
from app.database.conn import db
from app.database.models import Users, ApiKeys
from app.errors.exceptions import MaxAPIKeyEx, NoAPIKeyMatchEx
from app.schema import UserMe, ApiKey, AddKeyInfo

router = APIRouter()


@router.get("/me", response_model=UserMe)
def get_user(request: Request) -> UserMe:
    user = request.state.user
    user_info = Users.get(id=user.id)
    return user_info


@router.get("/apikeys", response_model=List[ApiKey])
async def get_api_key_list(request: Request, session: Session = Depends(db.session)) -> List[ApiKey]:
    """
    API Key 조회
    :param request:
    :param session:
    :return:
    """
    user = request.state.user
    user_id = user.id
    api_keys = session.query(ApiKeys).filter(ApiKeys.user_id == user_id)
    return api_keys


@router.post("/apikeys", response_model=ApiKey)
async def create_api_key(request: Request, key_info: AddKeyInfo, session: Session = Depends(db.session)) -> ApiKey:
    user = request.state.user
    user_id = user.id

    api_count = session.query(ApiKeys).filter(ApiKeys.user_id == user_id).count()
    if api_count == MAX_API_KEY:
        raise MaxAPIKeyEx()

    alphabet = string.ascii_letters + string.digits
    secret_key = "".join(secrets.choice(alphabet) for index in range(40))

    uid = None
    while uid is None:
        uid_candidate = f"{str(uuid4())[:12]}{uuid4()}"
        uid_check = session.query(ApiKeys).filter(ApiKeys.access_key == uid_candidate).first()
        if not uid_check:
            uid = uid_candidate

    key_info = key_info.dict()
    new_key = ApiKeys(access_key=uid, secret_key=secret_key, user_id=user_id, **key_info)
    session.add(new_key)
    session.flush()
    session.commit()
    return new_key


@router.put("/apikeys/{key_id}", response_model=ApiKey)
def change_api_key(request: Request, key_id: int, key_info: AddKeyInfo, session: Session = Depends(db.session)) -> ApiKey:
    user = request.state.user
    user_id = user.id

    api_key = session.query(ApiKeys).filter(ApiKeys.id == key_id)

    if api_key and api_key.first().user_id == user_id:
        key_info = key_info.dict()
        api_key.update(key_info)
        session.flush()
        session.commit()
    else:
        raise NoAPIKeyMatchEx()

    return api_key.first()
