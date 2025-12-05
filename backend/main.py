# backend/main.py
"""
FastAPI backend for AutoTARA-RAG

Exposes endpoints for:
- SysML upload
- Running stages 1–7
- CSV preview
- Modify / regenerate flows
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes_upload import router as upload_router
from api.routes_stages import router as stages_router
from api.routes_csv import router as csv_router
from api.routes_modify import router as modify_router
from api.routes_assets import router as assets_router

app = FastAPI(
    title="AutoTARA-RAG Backend",
    description="LLM + RAG powered TARA pipeline",
    version="1.0.0"
)

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(upload_router)
app.include_router(stages_router)
app.include_router(csv_router)
app.include_router(modify_router)
app.include_router(assets_router)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
