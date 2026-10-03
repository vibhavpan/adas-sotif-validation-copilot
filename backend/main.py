import os
import shutil
import traceback
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import  LangGraph workflow
from app.graph.workflow import adas_graph as graph_app

app = FastAPI(title="ADAS Validation Copilot API")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ValidationResponse(BaseModel):
    status: str
    diagnosis: str
    patch_file: str
    original_xml: Optional[str] = ""
    patched_xml: Optional[str] = ""
    simulation_result: Dict[str, Any]
    retries_taken: int


@app.post("/api/v1/validate", response_model=ValidationResponse)
async def validate_scenario(
    scenario: UploadFile = File(...),
    telemetry: UploadFile = File(...)
):
    try:
        # 1. Ensure working workspace directory exists
        work_dir = "/tmp/adas"
        os.makedirs(work_dir, exist_ok=True)

        scenario_path = os.path.join(work_dir, scenario.filename or "input.xosc")
        telemetry_path = os.path.join(work_dir, telemetry.filename or "input.csv")
        
        #reset file pointers to zero before reading
        await scenario.seek(0)
        scenario_bytes=await scenario.read()
        
        # 2. Save uploaded files to disk
        with open(scenario_path, "wb") as f:
            f.write(scenario_bytes)
        
        await telemetry.seek(0)
        telemetry_bytes=await telemetry.read()

        with open(telemetry_path, "wb") as f:
            f.write(telemetry_bytes)
        
        #Convert bytes to string for immediate state availability
        raw_xml_text=scenario_bytes.decode('utf-8',errors='ignore')
        
        # 3. Construct initial graph state
        initial_state = {
            "scenario_path": scenario_path,
            "telemetry_path": telemetry_path,
            "proposed_patch_path":"/tmp/adas/final_run.xosc",
            "original_xml": raw_xml_text,
            "patched_xml": None,
            "telemetry_slice": None,
            "xml_valid": False,
            "xml_error": None,
            "diagnosis": None,
            "patch_valid": False,
            "patch_error": None,
            "retries_taken": 0,
            "simulation_result": None,
            "final_status": "error"
        }

        # 4. Execute LangGraph workflow
        final_state = graph_app.invoke(initial_state)

        # Print debug to terminal to inspect state contents
        print("DEBUG - original_xml length:", len(final_state.get("original_xml") or ""))
        print("DEBUG - patched_xml length:", len(final_state.get("patched_xml") or ""))

        orig_xml = final_state.get("original_xml") or raw_xml_text
        patch_xml = final_state.get("patched_xml")

        # If patch_xml is empty or None, fallback to orig_xml so diff renders
        if not patch_xml or not patch_xml.strip():
            patch_xml = orig_xml
            
        # 5. Return typed response payload
        return ValidationResponse(
            status="success" if final_state.get("final_status") == "success" else "error",
            diagnosis=final_state.get("diagnosis") or "No diagnosis generated.",
            patch_file=final_state.get("proposed_patch_path") or "/tmp/adas/sample_fixed.xosc",
            original_xml=orig_xml,
            patched_xml=patch_xml,
            simulation_result=final_state.get("simulation_result") or {},
            retries_taken=final_state.get("retry_count") or final_state.get("retries_taken", 0)
        )

    except Exception as e:
        print("\n❌ EXCEPTION IN /api/v1/validate:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
