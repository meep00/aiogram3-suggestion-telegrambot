from aiogram.types import MessageEntity
from sqlalchemy import BigInteger, DateTime, func, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    created: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    updated: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    is_banned: Mapped[bool] = mapped_column(default=False, nullable=False)


class Suggestion(Base):
    __tablename__ = 'suggestions'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    mess_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    suggestion_id: Mapped[int] = mapped_column(Integer, nullable=False)
    file_id: Mapped[str] = mapped_column(String(150), nullable=True)
    caption: Mapped[str] = mapped_column(String(4096), nullable=True)  # 4096 chars for tg premium
    help_message: Mapped[int] = mapped_column(BigInteger, nullable=True)
    entities: Mapped[MutableList[MessageEntity]] = mapped_column(JSONB, nullable=True)


