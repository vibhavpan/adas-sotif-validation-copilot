from typing import TypedDict, Optional, List, Dict, Any

class ADASState(TypedDict):
    # Local File Paths
    scenario_path: str
    telemetry_path: str
    
    # Raw XML & Telemetry Content
    original_xml: str
    patched_xml: Optional[str]
    telemetry_slice: Optional[List[Dict[str, Any]]]
    
    # Preflight Check Results
    xml_valid: bool
    xml_error: Optional[str]
    
    # Gemini Analysis & Root Cause
    diagnosis: Optional[str]
    
    # Closed-Loop Repair Counters & Syntax Validation
    patch_valid: bool
    patch_error: Optional[str]
    retries_taken: int
    
    # C++ Simulator Output
    simulation_result: Optional[Dict[str, Any]]
    final_status: str
