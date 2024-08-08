import re
import time
import typing
from datetime import datetime

import jwt
from jwt import PyJWTError, ExpiredSignatureError
from starlette.datastructures import Headers
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Scope, Receive, Send

from app.common.consts import JWT_SECRET, JWT_ALGORITHM, EXCEPT_PATH_REGEX, EXCEPT_PATH_LIST
from app.errors import exceptions as ex
from app.errors.exceptions import APIException
from app.models import UserToken


async def access_control_middleware(request: Request, call_next):
    headers = request.headers

    ip_from = headers.get("x-forwarded-for", None)

    if await url_pattern_check(request.url.path, EXCEPT_PATH_REGEX) or request.url.path in EXCEPT_PATH_LIST:
        response = await call_next(request)
        return response

    try:
        # request.state: custom additional information
        now = datetime.now()
        request.state.req_time = now
        request.state.start = time.time()
        request.state.inspect = None
        request.state.user = None
        request.state.is_admin_access = None

        if request.url.path.startswith("/api"):
            access_token = headers.get("Authorization", None)
        else:
            # template render
            cookies = request.cookies
            access_token = cookies.get("Authorization", None)

        if not access_token:
            raise ex.NotAuthorizedEx

        token_info = await token_decode(access_token)
        request.state.user = UserToken(**token_info)

        response = await call_next(request)
    except ex.APIException as e:
        error = await exception_handler(e)
        error_dict = dict(status_code=error.status_code, code=error.code, detail=error.detail, msg=error.msg)
        response = JSONResponse(status_code=error.status_code, content=error_dict)
    return response


async def url_pattern_check(path, pattern):
    result = re.match(pattern, path)
    return bool(result)


async def token_decode(access_token):
    try:
        access_token = access_token.replace("Bearer ", "")
        payload = jwt.decode(access_token, key=JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except ExpiredSignatureError as ese:
        raise ex.TokenExpiredEx(ese)
    except PyJWTError as jwt_error:
        raise ex.TokenDecodeEx(jwt_error)
    return payload


async def exception_handler(error: Exception) -> ex.APIException:
    if not isinstance(error, ex.APIException):
        error = APIException(ex=error, detail=str(error))
    return error
