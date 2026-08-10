from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from app.database import engine, Base, get_db
from app.models import APIRequest
from app.schemas import APIRequestCreate, APIRequestResponse


Base.metadata.create_all(bind=engine)


app = FastAPI()


@app.get("/")
def home():
    return {"message": "API Sentinel is running"}


@app.get("/api/test")
def test_api():
    return {"message": "Test API endpoint is working"}


@app.post("/api/requests", response_model=APIRequestResponse)
def create_api_request(
    request: APIRequestCreate,
    db: Session = Depends(get_db)
):
    new_request = APIRequest(
        user_id=request.user_id,
        endpoint=request.endpoint,
        method=request.method,
        timestamp=request.timestamp,
        status_code=request.status_code,
        response_time=request.response_time,
        ip_address=request.ip_address
    )

    db.add(new_request)
    db.commit()
    db.refresh(new_request)

    return {
        "message": "API request saved successfully",
        "id": new_request.id
    }

# Swagger ->JSON request ->Pydantic validates it ->APIRequest SQLAlchemy object ->db.add() -> db.commit() -> PostgreSQL