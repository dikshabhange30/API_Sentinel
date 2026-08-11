from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordRequestForm
from app.oauth2 import create_access_token, get_current_user

from sqlalchemy.orm import Session

from app.database import engine, Base, get_db
from app.models import APIRequest, User
from app.schemas import (
    APIRequestCreate,
    APIRequestResponse,
    APIRequestListResponse,
    UserCreate,
    UserResponse
    
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    skip = (page - 1) * limit

    total = db.query(APIRequest).filter(APIRequest.user_id == current_user.id).count()

    if sort == "latest":
        order = APIRequest.timestamp.desc()
    elif sort == "oldest":
        order = APIRequest.timestamp.asc()
    else:
        raise HTTPException(
            status_code=400,
            detail="sort must be 'latest' or 'oldest'"
    )

    requests = db.query(APIRequest).filter( APIRequest.user_id == current_user.id).order_by(order).offset(skip).limit(limit).all()

    return {
    "page": page,
    "limit": limit,
    "total": total,
    "data": requests
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
