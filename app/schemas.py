from pydantic import BaseModel
from datetime import datetime


class APIRequestCreate(BaseModel):
    endpoint: str
    method: str
    timestamp: datetime
    status_code: int
    response_time: float
    ip_address: str

class APIRequestResponse(BaseModel):
    id: int
    message: str

class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str


class APIRequestData(BaseModel):
    id: int
    endpoint: str
    timestamp: datetime
    response_time: float
    method: str
    user_id: int
    status_code: int
    ip_address: str

class APIRequestListResponse(BaseModel):
    page: int
    limit: int
    total: int
    data: list[APIRequestData]

class APIAnalyticsResponse(BaseModel):
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    success_rate: float
    failure_rate: float
    health_status: str
    slow_requests: int

class SecurityAlertResponse(BaseModel):
    failed_login_attempts: int
    high_request_rate: bool
    suspicious_ips: list[str]
    security_status: str
    requests_last_minute: int
    security_reasons: list[str]

