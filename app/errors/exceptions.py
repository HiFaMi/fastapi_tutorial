from app.common.consts import MAX_API_KEY


class StatusCode:
    HTTP_500 = 500
    HTTP_400 = 400
    HTTP_401 = 401
    HTTP_403 = 403
    HTTP_404 = 404
    HTTP_405 = 405


class APIException(Exception):
    status_code: int
    code: str
    msg: str
    detail: str

    def __init__(self, *, status_code: int = StatusCode.HTTP_500, code: str = "0000000", msg: str = None, detail: str = None, ex: Exception = None):
        self.status_code = status_code
        self.code = code
        self.msg = msg
        self.detail = detail
        self.ex = ex
        super().__init__(ex)


class NotFoundUserEx(APIException):
    def __init__(self, user_id: int = None, ex: Exception = None):
        super().__init__(
            status_code=StatusCode.HTTP_404,
            code=f"{StatusCode.HTTP_400}{'1'.zfill(4)}",
            msg="해당 유저를 찾을 수 없습니다.",
            detail=f"Not Found User ID: {user_id}",
            ex=ex,
        )


class NotAuthorizedEx(APIException):
    def __init__(self, ex: Exception = None):
        super().__init__(
            status_code=StatusCode.HTTP_401,
            code=f"{StatusCode.HTTP_401}{'1'.zfill(4)}",
            msg="로그인이 필요한 서비스 입니다.",
            detail=f"Authorization Required",
            ex=ex,
        )


class TokenExpiredEx(APIException):
    def __init__(self, ex: Exception = None):
        super().__init__(
            status_code=StatusCode.HTTP_401,
            code=f"{StatusCode.HTTP_400}{'2'.zfill(4)}",
            msg="세션이 만료되어 로그아웃 되었습니다.",
            detail=f"Token Expired",
            ex=ex,
        )


class TokenDecodeEx(APIException):
    def __init__(self, ex: Exception = None):
        super().__init__(
            status_code=StatusCode.HTTP_400,
            code=f"{StatusCode.HTTP_400}{'3'.zfill(4)}",
            msg="비정상적인 접근 입니다.",
            detail=f"Token has been compromised.",
            ex=ex,
        )


class MaxAPIKeyEx(APIException):
    def __init__(self, ex: Exception = None):
        super().__init__(
            status_code=StatusCode.HTTP_400,
            code=f"{StatusCode.HTTP_400}{'4'.zfill(4)}",
            msg=f"API KEY 개수는 최대 {MAX_API_KEY}개 가능합니다.",
            detail="Max Key Count Reached",
            ex=ex,
        )


class NoAPIKeyMatchEx(APIException):
    def __init__(self, ex: Exception = None):
        super().__init__(
            status_code=StatusCode.HTTP_400,
            code=f"{StatusCode.HTTP_400}{'5'.zfill(4)}",
            msg=f"조건에 맞는 API Key가 없습니다.",
            detail="No Match API Key",
            ex=ex,
        )
