import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, files, imports, intelligence, knowledge, learn, money, notifications, profile, users, work


app = FastAPI(
    title="NEXUS AI API",
    description="Backend API for the NEXUS AI ecosystem",
    version="0.12.0",
)

allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(profile.router)
app.include_router(files.router)
app.include_router(imports.router)
app.include_router(knowledge.router)
app.include_router(learn.router)
app.include_router(money.router)
app.include_router(work.router)
app.include_router(intelligence.router)
app.include_router(notifications.router)


@app.get("/")
def read_root():
    return {"message": "Welcome to NEXUS AI"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
