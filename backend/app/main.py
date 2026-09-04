from fastapi import FastAPI

from app.routers import auth, users


app = FastAPI(
    title="NEXUS AI API",
    description="Backend API for the NEXUS AI ecosystem",
    version="0.2.0",
)

app.include_router(auth.router)
app.include_router(users.router)


@app.get("/")
def read_root():
    return {"message": "Welcome to NEXUS AI"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
