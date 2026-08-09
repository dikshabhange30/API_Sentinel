from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def home():
    return {"message": "API Sentinel is running"}

@app.get("/api/test")
def test_api():
    return {"message": "Test API endpoint is working"}