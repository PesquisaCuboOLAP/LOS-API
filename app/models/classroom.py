from sqlalchemy import Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Classroom(Base):
    __tablename__ = "classroom"
    __table_args__ = (UniqueConstraint("start_year", "end_year", name="uq_classroom_start_end"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    start_year: Mapped[str] = mapped_column(String(4), nullable=False)
    end_year: Mapped[str] = mapped_column(String(4), nullable=False)

    name: Mapped[str] = mapped_column(String(255), nullable=False)

    students: Mapped[list["Student"]] = relationship(
        back_populates="classroom"
    )