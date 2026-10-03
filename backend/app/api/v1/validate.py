import os
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.graph.workflow import adas_graph

router = APIRouter()

@router.post("/validate")
async def validate_scenario(
    scenario: UploadFile = File(...),
    telemetry: UploadFile = File(...)
):
    os.makedirs("/tmp/adas", exist_ok=True)
    scen_path = f"/tmp/adas/{scenario.filename}"
    telem_path = f"/tmp/adas/{telemetry.filename}"

    with open(scen_path, "wb") as f:
        f.write(await scenario.read())
    with open(telem_path, "wb") as f:
        f.write(await telemetry.read())

    initial_state = {
        "scenario_path": scen_path,
        "telemetry_path": telem_path,
        "xml_validation": {},
        "anomalies": {},
        "diagnosis": "",
        "proposed_patch_path": "",
        "sim_result": {},
        "retry_count": 0,
        "error_message": None
    }

    try:
        final_state = adas_graph.invoke(initial_state)
        return {
            "status": "success",
            "diagnosis": final_state["diagnosis"],
            "patch_file": final_state["proposed_patch_path"],
            "simulation_result": final_state["sim_result"],
            "retries_taken": final_state["retry_count"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
