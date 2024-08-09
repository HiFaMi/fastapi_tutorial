import re
import time
from datetime import datetime

import jwt
from jwt import PyJWTError, ExpiredSignatureError
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.common.consts import JWT_SECRET, JWT_ALGORITHM, EXCEPT_PATH_REGEX, EXCEPT_PATH_LIST
from app.errors import exceptions as ex
from app.schema import UserToken
from utils.logger import api_logger


async def access_control_middleware(request: Request, next_call):
    headers = request.headers
    ip_from = headers.get("x-forwarded-for", request.client.host)

    ip = ip_from.split(",")[0]
    # request.state: custom additional information
    now = datetime.now()
    request.state.ip = ip
    request.state.req_time = now
    request.state.start = time.time()
    request.state.inspect = None
    request.state.user = None
    request.state.is_admin_access = None

    url = request.url.path
    if await url_pattern_check(url, EXCEPT_PATH_REGEX) or url in EXCEPT_PATH_LIST:
        response = await next_call(request)

        if url == "/":
            await api_logger(request, response)

        return response

    try:
        if request.url.path.startswith("/api"):
            access_token = headers.get("Authorization", None)
        else:
            # template render
            cookies = request.cookies
            access_token = cookies.get("Authorization", None)

        if not access_token:
            raise ex.NotAuthorizedEx()

        token_info = await token_decode(access_token)
        request.state.user = UserToken(**token_info)

        response = await next_call(request)
        await api_logger(request, response=response)
    except Exception as e:
        error = await exception_handler(e)
        error_dict = dict(status_code=error.status_code, code=error.code, msg=error.msg, detail=error.detail)
        response = JSONResponse(error_dict, status_code=error.status_code)
        await api_logger(request, error=error)
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
        error = ex.APIException(ex=error, detail=str(error))
    return error
