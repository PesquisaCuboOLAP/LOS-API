from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


if TYPE_CHECKING:
    from app.models.classroom import Classroom
    from app.models.goal_short_name import GoalShortName


class LearningObjective(Base):
    __tablename__ = "learning_objective"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    keywords: Mapped[str] = mapped_column(Text, nullable=False)
    goal_short_name_id: Mapped[int] = mapped_column(
        ForeignKey("goal_short_name.id"),
        nullable=False,
        index=True,
    )
    classroom_id: Mapped[int] = mapped_column(
        ForeignKey("classroom.id"),
        nullable=False,
        index=True,
    )

    classroom: Mapped["Classroom"] = relationship(
        back_populates="learning_objectives"
    )
    goal_short_name: Mapped["GoalShortName"] = relationship(
        back_populates="learning_objectives"
    )