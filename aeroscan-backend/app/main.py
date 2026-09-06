from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.scan_router import router as scan_router

app = FastAPI(
    title="AI-Based Fake Identity & Document Screening System",
    description="LangGraph-orchestrated multi-agent pipeline for border-security document screening.",
    version="0.1.0",
)

# Next.js dev server origin - adjust/restrict for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scan_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}