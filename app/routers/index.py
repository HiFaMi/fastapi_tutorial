from datetime import datetime
from inspect import currentframe

from fastapi import APIRouter
from starlette.requests import Request
from starlette.responses import Response

router = APIRouter()


@router.get("/")
async def index():
    """
    ELB Health check
    :param :
    :return:
    """

    current_time = datetime.utcnow()
    return Response(f"Notification API (UTC: {current_time:%Y-%m-%d %H:%M:%S})")


@router.get("/test")
async def test(request: Request):
    print(f"state user: {request.state.user}")
    current_time = datetime.utcnow()
    try:
        1 / 0
    except Exception as e:
        request.state.inspect = currentframe()
        raise e
    return Response(f"Notification API (UTC: {current_time:%Y-%m-%d %H:%M:%S})")
