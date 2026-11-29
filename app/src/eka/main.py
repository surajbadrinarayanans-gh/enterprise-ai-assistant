from fastapi import FastAPI
from fastapi.testclient import TestClient

app = FastAPI()

@app.get("/healthz")
def health_check():
    return {"status": "healthy"}