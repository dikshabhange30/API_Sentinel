from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordRequestForm
from app.oauth2 import create_access_token, get_current_user

from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from app.database import engine, Base, get_db
from app.models import APIRequest, User
from app.schemas import (
    APIRequestCreate,
    APIRequestResponse,
    APIRequestListResponse,
    APIAnalyticsResponse,
    UserCreate,
    UserResponse,
    SecurityAlertResponse
    
)
from app.auth import hash_password, verify_password

# bcrypt/Passlib → password hashing
# python-jose    → JWT creation/verification
# OAuth2PasswordBearer → extract Bearer token from requests

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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_request = APIRequest(
        user_id=current_user.id,
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
        "id": new_request.id,
        "message": "API request saved successfully"
    }

@app.get("/api/requests", response_model=APIRequestListResponse)
def get_my_api_requests(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    sort: str = Query("latest"),
    status_code: int | None = Query(None),
    method: str | None = Query(None),
    endpoint: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    skip = (page - 1) * limit

    # total = db.query(APIRequest).filter(APIRequest.user_id == current_user.id).count()

    if sort == "latest":
        order = APIRequest.timestamp.desc()
    elif sort == "oldest":
        order = APIRequest.timestamp.asc()
    else:
        raise HTTPException(
            status_code=400,
            detail="sort must be 'latest' or 'oldest'"
    )

    query = db.query(APIRequest).filter(
    APIRequest.user_id == current_user.id)

    if status_code is not None:
        query = query.filter(
            APIRequest.status_code == status_code
    )

    if method is not None:
        query = query.filter(
            APIRequest.method == method
    )

    if endpoint is not None:
        query = query.filter(
            APIRequest.endpoint == endpoint
    )

    total = query.count()

    requests = query.order_by(order).offset(skip).limit(limit).all()

    return {
    "page": page,
    "limit": limit,
    "total": total,
    "data": requests
}

@app.get("/api/analytics", response_model=APIAnalyticsResponse)
def get_api_analytics(
    from_date: datetime | None = Query(None),
    to_date: datetime | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
    ):
    requests = db.query(APIRequest).filter(
        APIRequest.user_id == current_user.id
    )

    if from_date is not None:
        requests = requests.filter(
            APIRequest.timestamp >= from_date
    )

    if to_date is not None:
        requests = requests.filter(
            APIRequest.timestamp <= to_date
    )

    if from_date is not None and to_date is not None:
        if from_date > to_date:
            raise HTTPException(
                status_code=400,
                detail="from_date must be before to_date"
        )

    total_requests = requests.count()

    successful_requests = requests.filter(
        APIRequest.status_code >= 200,
        APIRequest.status_code < 300
    ).count()

    failed_requests = requests.filter(
        APIRequest.status_code >= 400,
        APIRequest.status_code < 600
    ).count()

    slow_requests = requests.filter(
        APIRequest.response_time > 1000
    ).count()


    average_response_time = requests.with_entities(
        func.avg(APIRequest.response_time)
    ).scalar()

    if total_requests > 0:
        success_rate = (successful_requests / total_requests) * 100
    else:
        success_rate = 0.0

    if total_requests > 0:
        failure_rate = (failed_requests / total_requests) * 100
    else:
        failure_rate = 0.0

    if total_requests == 0:
        health_status = "NO_DATA"
    elif failure_rate < 5:
        health_status = "HEALTHY"
    elif failure_rate <= 10:
        health_status = "WARNING"
    else:
        health_status = "CRITICAL"

    return {
        "total_requests": total_requests,
        "successful_requests": successful_requests,
        "failed_requests": failed_requests,
        "average_response_time": average_response_time or 0.0,
        "success_rate": success_rate,
        "failure_rate": failure_rate,
        "health_status": health_status,
        "slow_requests": slow_requests
    }


@app.get("/api/security", response_model=SecurityAlertResponse)
def get_security_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    now = datetime.utcnow()
    ten_minutes_ago = now - timedelta(minutes=10)

    recent_requests = db.query(APIRequest).filter(
        APIRequest.user_id == current_user.id,
        APIRequest.timestamp >= ten_minutes_ago
    )

    failed_login_attempts = recent_requests.filter(
        APIRequest.endpoint == "/login",
        APIRequest.status_code == 401
    ).count()

    one_minute_ago = now - timedelta(minutes=1)

    one_minute_requests = db.query(APIRequest).filter(
        APIRequest.user_id == current_user.id,
        APIRequest.timestamp >= one_minute_ago
    ).count()

    high_request_rate = one_minute_requests > 100

    suspicious_ip_rows = db.query(
        APIRequest.ip_address
    ).filter(
        APIRequest.user_id == current_user.id,
        APIRequest.timestamp >= ten_minutes_ago,
        APIRequest.status_code >= 400,
        APIRequest.status_code < 600
    ).group_by(
        APIRequest.ip_address
    ).having(
        func.count(APIRequest.id) >= 5
    ).all()

    suspicious_ips = [row[0] for row in suspicious_ip_rows]

    if high_request_rate or suspicious_ips or failed_login_attempts >= 5:
        security_status = "CRITICAL"
    elif failed_login_attempts > 0:
        security_status = "WARNING"
    else:
        security_status = "SAFE"

    security_reasons = []

    if failed_login_attempts > 0:
        security_reasons.append(
            f"{failed_login_attempts} failed login attempts"
        )

    if high_request_rate:
        security_reasons.append(
            f"High request rate: {one_minute_requests} requests in the last minute"
    )

    if suspicious_ips:
        for ip in suspicious_ips:
            security_reasons.append(
                f"Suspicious IP detected: {ip}"
        )

    return {
        "failed_login_attempts": failed_login_attempts,
        "high_request_rate": high_request_rate,
        "suspicious_ips": suspicious_ips,
        "requests_last_minute": one_minute_requests,
        "security_status": security_status,
        "security_reasons": security_reasons
    }
    


@app.post("/users", response_model=UserResponse)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter((User.username == user.username) | (User.email == user.email)).first()

    if existing_user:
        raise HTTPException( status_code=400, detail="Username or email already exists")
    
    hashed_password = hash_password(user.password)

    new_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

@app.post("/login")
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(
        User.username == form_data.username
    ).first()

    if not existing_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    password_is_valid = verify_password(
        form_data.password,
        existing_user.hashed_password
    )

    if not password_is_valid:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    access_token = create_access_token(
    data={"sub": str(existing_user.id)})

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@app.get("/users/me", response_model=UserResponse)
def read_current_user(
    current_user: User = Depends(get_current_user)
):
    return current_user
