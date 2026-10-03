
import os
import re
from typing import TypedDict, Optional,Dict,Any,List
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from app.mcp.xml_parser import validate_xosc_schema
from app.mcp.log_windower import extract_anomaly_window
from app.sim.esmini_runner import run_esmini_simulation
from app.mcp.xml_parser import validate_xosc_schema
from app.mcp.log_windower import extract_anomaly_window

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0.1
)

class ADASState(TypedDict):
    scenario_path: str
    telemetry_path: str
    original_xml: Optional[str]
    patched_xml: Optional[str]
    telemetry_slice: Optional[List[Dict[str, Any]]]
    xml_valid: bool
    xml_error: Optional[str]
    diagnosis: Optional[str]
    proposed_patch_path: Optional[str]
    simulation_result: Optional[Dict[str, Any]]
    final_status: str
    retry_count: int
    error_message: Optional[str]

def preflight_node(state: ADASState) -> ADASState:
    """Runs local FastMCP tools to validate XML syntax and extract high-risk telemetry logs."""
    scenario_path = state["scenario_path"]
    telemetry_path = state["telemetry_path"]
    
    # 1. Force the node to respect the populated string from main.py
    raw_xml = state.get("original_xml")
    if not raw_xml: 
        with open(scenario_path, "r", encoding="utf-8") as f:
            raw_xml = f.read()

    xml_result = validate_xosc_schema(scenario_path)
    telemetry_slice = extract_anomaly_window(telemetry_path)

    return {
        "original_xml": raw_xml,
        "xml_valid": xml_result["valid"],
        "xml_error": xml_result.get("error"),
        "telemetry_slice": telemetry_slice,
    }

def reasoning_node(state: ADASState) -> dict:
    """Diagnoses the issue without writing code."""
    prompt = f"""
    Diagnose the SOTIF failure based on these parameters.
    Telemetry: {state.get('telemetry_slice', [])}
    Return a brief markdown diagnosis.
    """
    response = llm.invoke(prompt)
    return {"diagnosis": str(response.content)}

def fix_common_xml_errors(xml_str: str) -> str:
    """Fixes missing TriggeringEntities and attribute typos prior to schema validation."""
    # Fix 'role=' attribute typo
    xml_str = xml_str.replace('role="', 'rule="')
    
    # Fix missing TriggeringEntities inside ByEntityCondition
    missing_triggering_pattern = r"(<ByEntityCondition>)\s*(<EntityCondition>)"
    replacement = (
        r"\1\n          <TriggeringEntities triggeringEntitiesRule=\"any\">\n"
        r"            <EntityRef entityRef=\"Ego\"/>\n"
        r"          </TriggeringEntities>\n          \2"
    )
    xml_str = re.sub(missing_triggering_pattern, replacement, xml_str)
    return xml_str
    
def patch_generation_node(state: ADASState) -> dict:
    """Generates the XML fix based on the diagnosis."""
    original_xml = state.get("original_xml")
    if not original_xml:
        with open(state["scenario_path"], "r", encoding="utf-8") as f:
            original_xml = f.read()

    prompt = f"""
    You are an automated OpenSCENARIO (.xosc) repair agent.
    Modify this OpenSCENARIO XML to eliminate collision risk.

    Original XML:
    {original_xml}

    Diagnosis:
    {state.get('diagnosis', '')}

    STRICT OPENSCENARIO 1.0 XML TEMPLATES (Do NOT deviate from this tag structure):

    1. Distance Trigger Template:
       <ByEntityCondition>
         <TriggeringEntities triggeringEntitiesRule="any">
           <EntityRef entityRef="Ego"/>
         </TriggeringEntities>
         <EntityCondition>
           <RelativeDistanceCondition entityRef="Target" relativeDistanceType="longitudinal" value="18.0" rule="lessThan"/>
         </EntityCondition>
       </ByEntityCondition>

    2. StopTrigger Template:
       <StopTrigger>
         <ConditionGroup>
           <Condition name="StopCondition" delay="0.0" conditionEdge="rising">
             <ByValueCondition>
               <SimulationTimeCondition value="10.0" rule="greaterOrEqual"/>
             </ByValueCondition>
           </Condition>
         </ConditionGroup>
       </StopTrigger>

    CRITICAL RULES:
    - Never omit <TriggeringEntities> inside <ByEntityCondition>.
    - Use the attribute name 'rule', NEVER 'role'.

    Return ONLY valid OpenSCENARIO XML code enclosed in an ```xml ... ``` code block.
    """
    
    response = llm.invoke(prompt)
    raw_output = str(response.content)

    match = re.search(r"```xml\s*(.*?)\s*```", raw_output, re.DOTALL)
    raw_xml_extract = match.group(1).strip() if match else raw_output.replace("```", "").strip()
    patched_xml=fix_common_xml_errors(raw_xml_extract)

    patch_path = state["scenario_path"].replace(".xosc", "_fixed.xosc")
    with open(patch_path, "w", encoding="utf-8") as f:
        f.write(patched_xml)

    return {
        "patched_xml": patched_xml,
        "proposed_patch_path": patch_path,
        "retry_count": state.get("retry_count", 0) + 1
    }

def validate_patch_node(state: ADASState) -> ADASState:
    check = validate_xosc_schema(state["proposed_patch_path"])
    if not check["valid"]:
        return {**state, "retry_count": state["retry_count"] + 1, "error_message": check["error"]}
    return {**state, "error_message": None}

def simulation_node(state: dict[str, any]) -> dict[str, any]:
    """Executes scenario XML file in esmini C++ engine."""
    # Fallback to scenario_path if proposed_patch_path is missing/None
    patch_path = state.get("proposed_patch_path") or state.get("scenario_path") or "/tmp/adas/final_run.xosc"

    # If patched_xml string exists in state, write it to disk before simulation
    if state.get("patched_xml"):
        os.makedirs(os.path.dirname(patch_path), exist_ok=True)
        with open(patch_path, "w", encoding="utf-8") as f:
            f.write(state["patched_xml"])

    # Run esmini runner safely
    sim_res = run_esmini_simulation(patch_path)

    return {
        "simulation_result": sim_res,
        "final_status": "success" if sim_res.get("success") else "error"
    }

def check_patch_router(state: ADASState) -> str:
    if state.get("error_message") and state["retry_count"] < 3:
        return "retry_patch"
    elif state.get("error_message") and state["retry_count"] >= 3:
        return "failed"
    return "execute_sim"

builder = StateGraph(ADASState)
builder.add_node("preflight", preflight_node)
builder.add_node("reasoning", reasoning_node)
builder.add_node("generate_patch", patch_generation_node)
builder.add_node("validate_patch", validate_patch_node)
builder.add_node("simulation", simulation_node)

builder.set_entry_point("preflight")
builder.add_edge("preflight", "reasoning")
builder.add_edge("reasoning", "generate_patch")
builder.add_edge("generate_patch", "validate_patch")

builder.add_conditional_edges(
    "validate_patch", check_patch_router,
    {"retry_patch": "generate_patch", "execute_sim": "simulation", "failed": END}
)
builder.add_edge("simulation", END)

adas_graph = builder.compile()
