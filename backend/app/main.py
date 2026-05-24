import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routers import archives, auth

Base.metadata.create_all(bind=engine)

CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:8080",
).split(",")

app = FastAPI(title="Archive Explorer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(archives.router, prefix="/api/archives", tags=["archives"])


@app.get("/api/health")
def health():
    return {"status": "ok"}
