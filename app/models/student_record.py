import enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


if TYPE_CHECKING:
    from app.models.learning_objective import LearningObjective
    from app.models.student import Student


class RatingLevel(str, enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    BEGINNER = "BEGINNER"
    PROGRESSING = "PROGRESSING"
    PROFICIENT = "PROFICIENT"
    EXEMPLARY = "EXEMPLARY"


class StudentRecord(Base):
    __tablename__ = "student_record"

    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "learning_objective_id",
            name="uq_student_learning_objective",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True, 
        index=True
    )
    
    student_id: Mapped[int] = mapped_column(
        ForeignKey("student.id"),
        nullable=False,
        index=True,
    )
    
    learning_objective_id: Mapped[int] = mapped_column(
        ForeignKey("learning_objective.id"),
        nullable=False,
        index=True,
    )
    
    rating: Mapped[RatingLevel] = mapped_column(
        Enum(RatingLevel),
        nullable=False,
        index=True,
    )

    student: Mapped["Student"] = relationship(
        back_populates="student_records"
    )
    
    learning_objective: Mapped["LearningObjective"] = relationship(
        back_populates="student_records"
    )
