from fastapi import FastAPI # importing FastAPI from the library.
from pydantic import BaseModel # we use pydantic to validate everything

app = FastAPI( # represents nexus backend application
    title="Nexus AI API",
    description="Backend API for the Nexus AI ecosystem",
    version="0.1.0"
)

class UserProfile(BaseModel): # We're defining the expected structure of incoming data. It is called data model/schema
    name: str
    email: str
    age: int

@app.get("/") # this is called a decorator, when someone calls this request the below function is executed
def root():
    return {
        "message": "Nexus AI backend is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }

@app.get("/users/{user_id}")
def get_user(user_id: int):
    return {
        "user_id": user_id,
        "name": "Test User"
    }

@app.post("/users")
def create_user(user: UserProfile):
    return {
        "message": "User created successfully",
        "user": user
    }