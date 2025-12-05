# api/routes_modify.py
from fastapi import APIRouter, Body
import json

from llm.formatting import inject_user_feedback
from llm.client import _call_llm, _load_prompt
from llm import parser

router = APIRouter(prefix="/modify", tags=["Modify"])


@router.post("/{stage_name}")
def modify(stage_name: str, body: dict = Body(...)):
    original_input = body.get("prompt_input")
    user_feedback = body.get("feedback")
    file_content = body.get("file_content")

    new_structured_input = inject_user_feedback(
        original_input,
        user_feedback,
        file_content
    )

    prompt_map = {
        "stage1": "1.asset_register.txt",
        "stage2": "2.damage_scenario.txt",
        "stage3": "4.impact_rating.txt",
        "stage4": "3.threat_scenario.txt",
        "stage5": "5.vulnerability_attackpath.txt",
        "stage6": "6.attack_feasibility.txt",
        "stage7": "7.Risk_values.txt",
    }
    
    if stage_name not in prompt_map:
        return {"error": f"Invalid stage name {stage_name}"}
    
    system_prompt = _load_prompt(prompt_map[stage_name])

    raw_output = _call_llm(system_prompt, new_structured_input)
    parsed = parser.safe_parse_json(raw_output)

    return {
        "raw_output": raw_output,
        "parsed": parsed
    }
