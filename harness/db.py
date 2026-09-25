"""Database engine/session setup. SQLite file lives at the project root."""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from harness.models import Base

DB_PATH = os.environ.get("HARNESS_DB_PATH", "sqlite:///harness.db")

engine = create_engine(DB_PATH, echo=False)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def init_db():
    """Create tables if they don't exist yet. Safe to call every run."""
    Base.metadata.create_all(engine)


def get_session():
    return SessionLocal()
