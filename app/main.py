from dataclasses import asdict

import uvicorn
from fastapi import FastAPI, Depends
from fastapi.security import APIKeyHeader
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware

from app.common.consts import EXCEPT_PATH_LIST, EXCEPT_PATH_REGEX
from app.database import schema
from app.database.conn import db

from app.common.config import conf_setting
from app.middlewares.token_validation import access_control_middleware
from app.middlewares.trusted_hosts import TrustedHostsMiddleware
from app.routers import index, auth, user

API_KEY_HEADER = APIKeyHeader(name="Authorization", auto_error=False)


def create_app():

    # 환경에 따른 config 변경
    config_setting = conf_setting()
    # asdict class obj -> dict로 변환
    config_setting_dict = asdict(config_setting)

    app = FastAPI()

    # 데이터베이스
    db.init_app(app, **config_setting_dict)
    # Database init 이후 engine 설정되어 있음
    # Database Schema Table 생성
    schema.Base.metadata.create_all(bind=db.engine)

    # 레디스

    # 미들웨어
    # 미들웨어의 경우 stack이기 때문에 가장 나중에 add 된 middleware부터 실행됨
    # 3. User Access Token 검사
    app.add_middleware(middleware_class=BaseHTTPMiddleware, dispatch=access_control_middleware)
    # 2. CORS 검사
    app.add_middleware(
        CORSMiddleware,
        allow_origins=conf_setting().ALLOW_SITE,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # 1. HOST 검사
    app.add_middleware(
        TrustedHostsMiddleware,
        allowed_hosts=conf_setting().TRUSTED_HOSTS,
        except_path=["/health"],
    )

    # 라우터
    # 라우터 추가
    app.include_router(index.router)
    app.include_router(auth.router, tags=["Authentication"], prefix="/api")
    app.include_router(user.router, tags=["User"], prefix="/api", dependencies=[Depends(API_KEY_HEADER)])
    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=conf_setting().PROJ_RELOAD)
