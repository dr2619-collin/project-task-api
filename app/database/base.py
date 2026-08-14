"""Shared SQLAlchemy declarative base class."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class inherited by every SQLAlchemy ORM model.

    DeclarativeBase gives SQLAlchemy one shared registry and one metadata
    collection. When Project and Task inherit Base, their table and column
    declarations are added to Base.metadata. The application later uses that
    metadata to create missing tables with Base.metadata.create_all(...).
    """
