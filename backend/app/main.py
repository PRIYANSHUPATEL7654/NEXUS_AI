from fastapi import FastAPI

from app.database import Base, engine
from app.routers import users


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="NEXUS AI API",
    description="Backend API for the NEXUS AI ecosystem",
    version="0.1.0"
)


app.include_router(users.router)


@app.get("/")
def read_root():
    return {
        "message": "Welcome to NEXUS AI"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }