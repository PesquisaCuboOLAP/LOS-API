from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

class Classroom(Base):
    __tablename__ = "classroom"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    start_year: Mapped[str] = mapped_column(String(4), nullable=False)
    end_year: Mapped[str] = mapped_column(String(4), nullable=False)

    name: Mapped[str] = mapped_column(String(255), nullable=False)