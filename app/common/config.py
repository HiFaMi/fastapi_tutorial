from os import path, environ
from dataclasses import dataclass

BASE_DIR = path.dirname(path.dirname(path.dirname(path.abspath(__file__))))


@dataclass
class Config:

    BASE_DIR = BASE_DIR
    DB_POOL_RECYCLE: int = 900
    DB_ECHO: bool = True


@dataclass
class LocalConfig(Config):
    PROJ_RELOAD: bool = True
    DB_URL: str = "mysql+pymysql://travis@localhost:3306/notification_api?charset=utf8mb4"
    ALLOW_SITE = ["*"]
    TRUSTED_HOSTS = ["*"]


@dataclass
class ProdConfig(Config):
    PROJ_RELOAD: bool = False


def conf_setting():
    config = dict(prod=ProdConfig(), local=LocalConfig())
    return config.get(environ.get("API_ENV", "local"))
