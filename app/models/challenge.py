from enum import Enum

from sqlalchemy import Enum as SQLEnum, Integer, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Semester(int, Enum):
    FIRST = 1
    SECOND = 2
    THIRD = 3
    FOURTH = 4

class Challenge(Base):
    __tablename__ = "challenge"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    semester: Mapped[Semester] = mapped_column(
        SQLEnum(Semester),
        nullable=True
    )
    learning_objective_ids: Mapped[list[int]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )