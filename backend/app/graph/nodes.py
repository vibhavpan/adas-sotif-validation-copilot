import os
from typing import Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from app.agent.state import ADASState
from app.mcp.xml_parser import parse_and_validate_xml
from app.mcp.log_windower import extract_critical_window
from app.sim.esmini_runner import run_esmini_simulation

# Initialize Gemini 2.5 Flash
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.1)


def preflight_node(state: ADASState) -> Dict[str, Any]:
    """Runs local FastMCP tools to validate XML syntax and extract high-risk telemetry logs."""
    scenario_path = state["scenario_path"]
    telemetry_path = state["telemetry_path"]
    
    # 1. Force the node to respect the populated string from main.py
    raw_xml = state.get("original_xml")
    if not raw_xml: 
        with open(scenario_path, "r", encoding="utf-8") as f:
            raw_xml = f.read()

    xml_result = parse_and_validate_xml(scenario_path)
    telemetry_slice = extract_critical_window(telemetry_path)

    return {
        "original_xml": raw_xml,
        "xml_valid": xml_result["valid"],
        "xml_error": xml_result.get("error"),
        "telemetry_slice": telemetry_slice,
    }


def reasoning_node(state: ADASState) -> Dict[str, Any]:
    """Prompts Gemini 2.5 Flash to perform a SOTIF root cause analysis on extracted anomalies."""
    xml_status = "Valid" if state["xml_valid"] else f"Invalid ({state['xml_error']})"
    telemetry_data = state.get("telemetry_slice", [])

    prompt = f"""
    You are an expert ADAS Validation & SOTIF Engineer.
    Analyze the following scenario input and telemetry window to diagnose the failure root cause.

    OpenSCENARIO Syntax Status: {xml_status}
    Telemetry Anomaly Window (TTC < 1.5s):
    {telemetry_data}

    Provide a structured Markdown diagnosis containing:
    - Summary of Findings
    - Detailed Analysis of Errors / Anomalies
    - Root Cause Analysis (SOTIF / ISO 26262 context)
    - Recommendations for Repair
    """
    response = llm.invoke(prompt)
    return {"diagnosis": str(response.content)}


def generate_patch_node(state: ADASState) -> Dict[str, Any]:
    """Prompts Gemini to generate a repaired OpenSCENARIO (.xosc) XML file."""
    original_xml = state.get("original_xml")
    
    if not original_xml:
        with open(state["scenario_path"], "r", encoding="utf-8") as f:
            original_xml = f.read()

    prompt = f"""
    You are an automated OpenSCENARIO (.xosc) repair agent.
    Modify this OpenSCENARIO XML to eliminate collision risk (e.g., adjust Target/Ego teleport positions or braking logic).

    Original XML:
    {original_xml}

    Diagnosis:
    {state.get('diagnosis', '')}

    Return ONLY the valid OpenSCENARIO XML code enclosed in an ```xml ... ``` code block.
    """
    response = llm.invoke(prompt)
    raw_output = str(response.content)

    import re
    match = re.search(r"```xml\s*(.*?)\s*```", raw_output, re.DOTALL)
    patched_xml = match.group(1).strip() if match else raw_output.replace("```", "").strip()

    return {
        "original_xml": original_xml,
        "patched_xml": patched_xml,
        "retries_taken": state.get("retries_taken", 0) + 1,
    }

def validate_patch_node(state: ADASState) -> Dict[str, Any]:
    """Executes local defusedxml validation on Gemini's generated XML patch."""
    patched_xml = state.get("patched_xml", "")
    temp_patch_path = "/tmp/adas/temp_patched.xosc"

    os.makedirs(os.path.dirname(temp_patch_path), exist_ok=True)
    with open(temp_patch_path, "w", encoding="utf-8") as f:
        f.write(patched_xml)

    validation = parse_and_validate_xml(temp_patch_path)

    return {
        "patch_valid": validation["valid"],
        "patch_error": validation.get("error"),
    }


def simulation_node(state: ADASState) -> Dict[str, Any]:
    """Executes the validated OpenSCENARIO XML file inside the esmini C++ engine."""
    target_path = "/tmp/adas/final_run.xosc"
    xml_content = state.get("patched_xml") or state.get("original_xml", "")

    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(xml_content)

    sim_output = run_esmini_simulation(target_path)

    return {
        "simulation_result": sim_output,
        "final_status": "success" if sim_output["success"] else "error",
    }
