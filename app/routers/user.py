from fastapi import APIRouter
from starlette.requests import Request

from app.database.models import Users
from app.schema import UserMe

router = APIRouter()


@router.get("/me", response_model=UserMe)
def get_user(request: Request) -> UserMe:
    user = request.state.user
    user_info = Users.get(id=user.id)
    return user_info
