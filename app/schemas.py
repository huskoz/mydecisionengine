from pydantic import BaseModel

class Task(BaseModel):
    id: str
    signals: dict[str, float] #dictionary whose key is a str, value is float
    readiness: int
    depends_on: list[str]
    needs: dict[str, int]



