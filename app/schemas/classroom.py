from pydantic import BaseModel, ConfigDict, Field

class ClassroomBase(BaseModel):
    start_year: str = Field(..., min_length=4, max_length=4, pattern=r"^\d{4}$")
    end_year: str = Field(..., min_length=4, max_length=4, pattern=r"^\d{4}$")


class ClassroomCreate(ClassroomBase):
    pass    

class ClassroomUpdate(ClassroomBase):
    pass

class ClassroomRead(ClassroomBase):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)