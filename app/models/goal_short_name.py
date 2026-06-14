from typing import TYPE_CHECKING

from enum import Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SQLEnum, Integer, String

from app.database import Base


if TYPE_CHECKING:
    from app.models.learning_objective import LearningObjective


class Strand(str, Enum):
    MARKETING = "MARKETING"
    CODING = "CODING"
    DESIGN = "DESIGN"
    PROCESS = "PROCESS"
    PROFESSIONAL_SKILLS = "PROFESSIONAL_SKILLS"

class GoalShortName(Base):
    __tablename__ = "goal_short_name"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    strand: Mapped[Strand] = mapped_column(
        SQLEnum(Strand),
        nullable=False
    )

    learning_objectives: Mapped[list["LearningObjective"]] = relationship(
        back_populates="goal_short_name"
    )