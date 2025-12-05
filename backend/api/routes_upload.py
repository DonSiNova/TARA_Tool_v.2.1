# api/routes_upload.py
from fastapi import APIRouter, UploadFile, File
import os
from config.settings import settings

router = APIRouter(tags=["Upload"])


@router.post("/upload-sysml")
async def upload_sysml(file: UploadFile = File(...)):
    out_path = os.path.join(settings.OUTPUT_DIR, "uploaded_sysml.json")

    with open(out_path, "wb") as f:
        f.write(await file.read())

    return {"status": "ok", "path": out_path}
