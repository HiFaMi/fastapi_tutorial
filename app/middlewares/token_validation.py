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

from app.common.consts import JWT_SECRET, JWT_ALGORITHM
from app.errors import exceptions as ex
from app.models import UserToken


class AccessControlMiddleware:

    def __init__(self, app: ASGIApp, except_path_list: typing.Sequence[str] = None, except_path_regx: str = None) -> None:
        if except_path_list is None:
            except_path_list = ["*"]

        self.app = app
        self.except_path_list = except_path_list
        self.except_path_regx = except_path_regx

    # Middleware 호출시 동작
    async def __call__(self, scope: Scope, receive: Receive, send: Send):

        request = Request(scope=scope)
        headers = Headers(scope=scope)

        ip_from = headers.get("x-forwarded-for", None)

        if await self.url_pattern_check(request.url.path, self.except_path_regx) or request.url.path in self.except_path_list:
            return await self.app(scope, receive, send)

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

            token_info = await self.token_decode(access_token)
            request.state.user = UserToken(**token_info)

            res = await self.app(scope, receive, send)
        except ex.APIException as e:
            res = await self.exception_handler(e)
            res = await res(scope, receive, send)
        return res

    @staticmethod
    async def url_pattern_check(path, pattern):
        result = re.match(pattern, path)
        return bool(result)

    @staticmethod
    async def token_decode(access_token):
        try:
            access_token = access_token.replace("Bearer ", "")
            payload = jwt.decode(access_token, key=JWT_SECRET, algorithms=[JWT_ALGORITHM])
        except ExpiredSignatureError as ese:
            raise ex.TokenExpiredEx(ese)
        except PyJWTError as jwt_error:
            raise ex.TokenDecodeEx(jwt_error)
        return payload

    @staticmethod
    async def exception_handler(error: ex.APIException) -> JSONResponse:
        error_dict = dict(status_code=error.status_code, code=error.code, msg=error.msg, detail=error.detail)
        res = JSONResponse(status_code=error.status_code, content=error_dict)
        return res
