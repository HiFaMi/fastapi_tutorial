from fastapi import APIRouter
from starlette.requests import Request

from app.database.schema import Users
from app.models import UserMe, UserToken

router = APIRouter()


@router.get("/me", response_model=UserMe)
def get_user(request: Request) -> UserMe:
    user = request.state.user
    user_info = Users.get(id=user.id)
    return user_info
