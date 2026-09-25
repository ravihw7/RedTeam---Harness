"""
SQLAlchemy models for the red-team/eval harness.

Category      -> a grouping of test cases (jailbreak, bias_probe, etc.)
TestCase      -> a single prompt + what we expect the target model to do with it
Run           -> one execution of a suite against one target model
Result        -> the outcome of a single TestCase within a single Run
"""

from datetime import datetime, timezone


def utc_now():
    return datetime.now(timezone.utc)

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)
    name = Column(String(64), unique=True, nullable=False)
    description = Column(Text, default="")

    test_cases = relationship("TestCase", back_populates="category")


class TestCase(Base):
    __tablename__ = "test_cases"

    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)

    prompt = Column(Text, nullable=False)
    # "refuse"       -> target SHOULD decline / push back
    # "answer"       -> target SHOULD answer helpfully (tests over-refusal)
    # "no_injection" -> target SHOULD ignore embedded instructions in the content
    expected_behavior = Column(String(32), nullable=False)
    severity = Column(String(16), default="medium")  # low | medium | high
    notes = Column(Text, default="")

    category = relationship("Category", back_populates="test_cases")
    results = relationship("Result", back_populates="test_case")


class Run(Base):
    __tablename__ = "runs"

    id = Column(Integer, primary_key=True)
    model_name = Column(String(128), nullable=False)
    started_at = Column(DateTime, default=utc_now)
    finished_at = Column(DateTime, nullable=True)
    notes = Column(Text, default="")

    results = relationship("Result", back_populates="run", cascade="all, delete-orphan")


class Result(Base):
    __tablename__ = "results"

    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey("runs.id"), nullable=False)
    test_case_id = Column(Integer, ForeignKey("test_cases.id"), nullable=False)

    response_text = Column(Text)
    passed = Column(Boolean)
    score = Column(Float, nullable=True)
    judge_rationale = Column(Text, default="")
    latency_ms = Column(Integer, nullable=True)

    run = relationship("Run", back_populates="results")
    test_case = relationship("TestCase", back_populates="results")
