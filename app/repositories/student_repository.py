from sqlalchemy.orm import Session

from app.models import Student


class StudentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, name: str) -> Student:
        raise NotImplementedError()

    def list(self) -> list[Student]:
        raise NotImplementedError()

    def get(self, student_id: int) -> Student | None:
        raise NotImplementedError()

    def update(self, student_id: int, name: str) -> Student | None:
        raise NotImplementedError()

    def delete(self, student_id: int) -> bool:
        raise NotImplementedError()
