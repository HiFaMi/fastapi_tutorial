# models for DB Table

from sqlalchemy import Column, Integer, DateTime, func, Enum, String, Boolean, ForeignKey
from sqlalchemy.orm import Session, relationship

from app.database.conn import Base, db


class BaseMixin:
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    created_at = Column(DateTime, nullable=False, default=func.utc_timestamp())
    updated_at = Column(DateTime, nullable=False, default=func.utc_timestamp(), onupdate=func.utc_timestamp())

    def all_columns(self):
        return [table_column for table_column in self.__table__.columns if table_column.primary_key is False and table_column.name != "created_at"]

    def __hash__(self):
        return hash(self.id)

    @classmethod
    def create(cls, session: Session, auto_commit: bool = False, **kwargs):
        """
        테이블 데이터 적재 함수
        :param session:
        :param auto_commit:
        :param kwargs:
        :return:
        """
        obj = cls()
        for column in obj.all_columns():
            column_name = column.name
            if column_name in kwargs:
                setattr(obj, column_name, kwargs.get(column_name))
        session.add(obj)
        session.flush()

        if auto_commit:
            session.commit()
        return obj

    @classmethod
    def get(cls, **kwargs):
        session = next(db.session())
        query = session.query(cls)

        for key, value in kwargs.items():
            column = getattr(cls, key)
            query = query.filter(column == value)

        if query.count() > 1:
            raise Exception("Only one row is supposed to be returned, but got more than one")
        return query.first()


class Users(Base, BaseMixin):
    __tablename__ = "users"
    status = Column(Enum("active", "deleted", "blocked"), default="active")
    email = Column(String(length=255), nullable=True)
    pw = Column(String(length=2000), nullable=True)
    name = Column(String(length=255), nullable=True)
    phone_number = Column(String(length=20), nullable=True, unique=True)
    profile_image = Column(String(length=1000), nullable=True)
    sns_type = Column(Enum("FB", "G", "N"), nullable=True, default=None)
    marketing_agree = Column(Boolean, default=False)


class ApiKeys(Base, BaseMixin):
    __tablename__ = "api_keys"
    access_key = Column(String(length=64), nullable=False, index=True)
    secret_key = Column(String(length=64), nullable=False)
    memo = Column(String(length=40), nullable=True)
    status = Column(Enum("active", "stopped", "deleted"), default="active")
    is_whitelisted = Column(Boolean, default=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    white_list = relationship("ApiWhiteLists", backref="api_keys")


class ApiWhiteLists(Base, BaseMixin):
    __tablename__ = "api_white_lists"
    ip_address = Column(String(length=64), nullable=False)
    api_key_id = Column(Integer, ForeignKey("api_keys.id"), nullable=False)
