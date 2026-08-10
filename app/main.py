from fastapi import FastAPI

from app.database import engine, Base
from app.models import APIRequest


Base.metadata.create_all(bind=engine)


app = FastAPI()


@app.get("/")
def home():
    return {"message": "API Sentinel is running"}


@app.get("/api/test")
def test_api():
    return {"message": "Test API endpoint is working"}