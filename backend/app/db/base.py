import os
os.environ.setdefault("DISABLE_SQLALCHEMY_CEXT", "1")

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy database models."""
    pass
