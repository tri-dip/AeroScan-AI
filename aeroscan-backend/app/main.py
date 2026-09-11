import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from app.api.scan_router import router as scan_router

app = FastAPI(
    title="AI-Based Fake Identity & Document Screening System",
    description="LangGraph-orchestrated multi-agent pipeline for border-security document screening.",
    version="0.1.0",
)

# Comma-separated list of allowed frontend origins, e.g.
# "https://app.example.com,https://staging.example.com". Defaults to the
# Next.js dev server origin for local development.
_allowed_origins = [
    origin.strip()
    for origin in os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scan_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}