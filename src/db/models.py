from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, text, ForeignKey, DateTime, BigInteger
from sqlalchemy import Enum as SQLEnum
from .database import Base
from typing import Annotated
import datetime
import enum


class Status(enum.Enum):
    in_progress = "in progress"
    finished = "finished"


idpk = Annotated[int, mapped_column(primary_key=True)]
created_timestamp = Annotated[datetime.datetime, mapped_column(
    DateTime, 
    server_default=text("CURRENT_TIMESTAMP")
)]


class UsersTable(Base):
    __tablename__ = "users"
    
    id: Mapped[idpk]
    name: Mapped[str | None]
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    created_at: Mapped[created_timestamp]
    

class TestsTable(Base):
    __tablename__ = "tests"
    
    id: Mapped[idpk]
    title: Mapped[str] = mapped_column(String(20))
    description: Mapped[str | None]
    created_at: Mapped[created_timestamp | None]


class QuestionTable(Base):
    __tablename__ = "questions"
    
    id: Mapped[idpk]
    test_id: Mapped[int] = mapped_column(ForeignKey("tests.id", ondelete="CASCADE"))
    text: Mapped[str]
    created_at: Mapped[created_timestamp | None]
    
    choices = relationship("ChoicesTable", back_populates="question")
    

class ChoicesTable(Base):
    __tablename__ = "choices"
    
    id: Mapped[idpk]
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"))
    label: Mapped[str] = mapped_column()
    text: Mapped[str]
    is_correct: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[created_timestamp]
    
    question = relationship("QuestionTable", back_populates="choices")


class AttemptsTable(Base):
    __tablename__ = "attempts"
    
    id: Mapped[idpk]
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    test_id: Mapped[int] = mapped_column(ForeignKey("tests.id", ondelete="CASCADE"))
    score: Mapped[int | None]
    total: Mapped[int | None]
    status: Mapped[Status] = mapped_column(SQLEnum(Status), default=Status.in_progress)
    started_at: Mapped[created_timestamp]
    finished_at: Mapped[created_timestamp | None]


class AnswersTable(Base):
    __tablename__ = "answers"
    
    id: Mapped[idpk]
    attempt_id: Mapped[int] = mapped_column(ForeignKey("attempts.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"))
    selected_choice_id: Mapped[int] = mapped_column(ForeignKey("choices.id", ondelete="CASCADE"))
    created_at: Mapped[created_timestamp]