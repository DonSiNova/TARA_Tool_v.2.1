# api/routes_stages.py
from fastapi import APIRouter, Body, HTTPException
from app.orchestrator import TARAOrchestrator
from config.settings import settings
import os

router = APIRouter(prefix="/run-stage", tags=["Stages"])

orchestrator = TARAOrchestrator()


@router.post("/{stage_id}")
def run_stage(
    stage_id: int,
    stakeholder: str | None = Body(default=None),
    assetId: str | None = Body(default=None),
):
    if stage_id == 1:
        sysml_path = os.path.join(settings.OUTPUT_DIR, "uploaded_sysml.json")
        return orchestrator.run_stage_1(sysml_path)

    elif stage_id == 2:
        if not assetId:
            raise HTTPException(status_code=400, detail="assetId is required for Stage 2")
        return orchestrator.run_stage_2(assetId, stakeholder or "Road User")

    elif stage_id == 3:
        return orchestrator.run_stage_3(assetId or "")

    elif stage_id == 4:
        return orchestrator.run_stage_4(assetId or "")

    elif stage_id == 5:
        return orchestrator.run_stage_5(assetId or "")

    elif stage_id == 6:
        return orchestrator.run_stage_6(assetId or "")

    elif stage_id == 7:
        return orchestrator.run_stage_7(assetId or "", stakeholder or "Road User")

    return {"error": "Invalid stage"}
