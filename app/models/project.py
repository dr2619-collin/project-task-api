"""SQLAlchemy model for the projects table."""

from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Project(Base):
    """Map Project objects to rows in the projects table."""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)

    # The relationship lets Python navigate project.tasks. The foreign key is
    # stored on Task because Task is the "many" side of the relationship.
    tasks: Mapped[list[Task]] = relationship(back_populates="project")
