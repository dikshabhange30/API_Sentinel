from pydantic import BaseModel
from datetime import datetime


class APIRequestCreate(BaseModel):
    user_id: int | None = None
    endpoint: str
    method: str
    timestamp: datetime
    status_code: int
    response_time: float
    ip_address: str

class APIRequestResponse(BaseModel):
    id: int
    message: str