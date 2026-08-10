from sqlalchemy import Column, Integer, String, DateTime, Float
from app.database import Base


class APIRequest(Base):
    
    __tablename__ = "api_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    endpoint = Column(String, nullable=False)
    method = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    status_code = Column(Integer, nullable=False)
    response_time = Column(Float, nullable=False)
    ip_address = Column(String, nullable=False)