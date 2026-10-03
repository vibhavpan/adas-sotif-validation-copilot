import xml.etree.ElementTree as ET
from typing import Dict, Any

def validate_xosc_schema(file_path: str) -> Dict[str, Any]:
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        if not root.tag.endswith("OpenSCENARIO"):
            return {"valid": False, "error": "Root tag is not <OpenSCENARIO>"}
        return {"valid": True, "root": root.tag, "error": None}
    except ET.ParseError as e:
        return {"valid": False, "error": f"XML Parse Error: {str(e)}"}
