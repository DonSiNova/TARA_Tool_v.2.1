# api/routes_csv.py
import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from storage.run_state import get_run_dir

router = APIRouter(prefix="/csv", tags=["CSV"])


@router.get("/{filename}", response_class=PlainTextResponse)
def get_csv(filename: str):
    path = os.path.join(get_run_dir(), filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="CSV not found")

    with open(path, "r", encoding="utf-8") as f:
        return f.read()
