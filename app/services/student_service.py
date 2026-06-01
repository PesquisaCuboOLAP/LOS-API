from app.models import Student
from app.repositories.student_repository import StudentRepository


class StudentNotFoundError(Exception):
    pass


class StudentService:
    def __init__(self, repository: StudentRepository) -> None:
        self.repository = repository

    def create_student(self, name: str) -> Student:
        raise NotImplementedError()

    def list_students(self) -> list[Student]:
        raise NotImplementedError()

    def get_student(self, student_id: int) -> Student:
        raise NotImplementedError()

    def update_student(self, student_id: int, name: str) -> Student:
        raise NotImplementedError()

    def delete_student(self, student_id: int) -> None:
        raise NotImplementedError()
