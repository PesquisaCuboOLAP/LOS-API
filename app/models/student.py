from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Student(Base):
    __tablename__ = "student"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    classroom_id: Mapped[int] = mapped_column(
        ForeignKey("classroom.id"), 
        nullable=False, 
        index=True
    )

    classroom: Mapped["Classroom"] = relationship(
        back_populates="students"
    )