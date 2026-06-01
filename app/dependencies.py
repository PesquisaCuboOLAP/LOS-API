from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.student_repository import StudentRepository
from app.services.student_service import StudentService


def get_student_repository(db: Session = Depends(get_db)) -> StudentRepository:
    return StudentRepository(db)


def get_student_service(
    repository: StudentRepository = Depends(get_student_repository),
) -> StudentService:
    return StudentService(repository)
