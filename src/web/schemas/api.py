from pydantic import BaseModel, Field

class ApiResult[T](BaseModel):
    code: int
    message: str
    data: T | None = Field(default=None)


class HealthResponse(BaseModel):
    status: str