from datetime import datetime
from uuid import uuid4
import enum
from sqlalchemy import String, Text, Integer, Boolean, ForeignKey, DateTime, Enum, UniqueConstraint, Index, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from .session import Base

def uid() -> str: return str(uuid4())

class Role(str, enum.Enum):
    student = "student"
    admin = "admin"

class QType(str, enum.Enum):
    mcq = "mcq"
    ox = "ox"
    short = "short_answer"

class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    email: Mapped[str] = mapped_column(String(191), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    files: Mapped[list["UploadedFile"]] = relationship(back_populates="user", cascade="all, delete-orphan")

class UploadedFile(Base):
    __tablename__ = "uploaded_files"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(500))
    file_type: Mapped[str] = mapped_column(String(20))   # pdf/docx/pptx/image
    ai_status: Mapped[str] = mapped_column(String(20), default="pending")  # pending/parsed/error
    summary: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="files")
    concepts: Mapped[list["Concept"]] = relationship(back_populates="file", cascade="all, delete-orphan")

class Concept(Base):
    __tablename__ = "concepts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    file_id: Mapped[str] = mapped_column(ForeignKey("uploaded_files.id", ondelete="CASCADE"), index=True)
    keyword: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    importance: Mapped[int] = mapped_column(Integer, default=3)

    file: Mapped["UploadedFile"] = relationship(back_populates="concepts")
    questions: Mapped[list["Question"]] = relationship(back_populates="concept", cascade="all, delete-orphan")
    __table_args__ = (
        UniqueConstraint("file_id", name="uq_concepts_file_id"),
    )

class Question(Base):
    __tablename__ = "questions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    concept_id: Mapped[str] = mapped_column(ForeignKey("concepts.id", ondelete="CASCADE"), index=True)
    question_type: Mapped[QType] = mapped_column(Enum(QType))
    question_text: Mapped[str] = mapped_column(Text)
    correct_answer: Mapped[str] = mapped_column(Text)
    options: Mapped[dict | None] = mapped_column(JSONB)  # e.g. {"A":"...", "B":"..."}
    difficulty: Mapped[int] = mapped_column(Integer, default=3)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    concept: Mapped["Concept"] = relationship(back_populates="questions")

class Test(Base):
    __tablename__ = "tests"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    test_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    total_questions: Mapped[int] = mapped_column(Integer)
    correct_count: Mapped[int] = mapped_column(Integer, default=0)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class TestItem(Base):
    __tablename__ = "test_items"
    __table_args__ = (UniqueConstraint("test_id", "question_id", name="uq_test_question"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    test_id: Mapped[str] = mapped_column(ForeignKey("tests.id", ondelete="CASCADE"), index=True)
    question_id: Mapped[str] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), index=True)

class Answer(Base):
    __tablename__ = "answers"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    test_id: Mapped[str] = mapped_column(ForeignKey("tests.id", ondelete="CASCADE"), index=True)
    question_id: Mapped[str] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), index=True)
    user_answer: Mapped[str] = mapped_column(Text)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)

Index("idx_questions_concept_difficulty", Question.concept_id, Question.difficulty)
