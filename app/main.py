from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import Base, engine
from app.models import Student  # noqa: F401 - Register models with Base
from app.routers.students import router as students_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="LOS API", version="0.1.0", lifespan=lifespan)
app.include_router(students_router)


@app.get("/health")
def healthcheck():
    return {"status": "ok"}