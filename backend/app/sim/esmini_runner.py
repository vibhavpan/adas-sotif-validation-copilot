import os
import re
import shutil
import subprocess
from typing import Dict, Any

def ensure_stop_condition(xosc_path: str, max_seconds: float = 10.0):
    """Ensures the OpenSCENARIO file contains a valid StopTrigger so esmini auto-terminates."""
    if not os.path.exists(xosc_path):
        return
        
    with open(xosc_path, "r", encoding="utf-8") as f:
        content = f.read()

    stop_block = f"""<StopTrigger>
      <ConditionGroup>
        <Condition name="AutoStopCondition" delay="0.0" conditionEdge="rising">
          <ByValueCondition>
            <SimulationTimeCondition value="{max_seconds}" rule="greaterOrEqual"/>
          </ByValueCondition>
        </Condition>
      </ConditionGroup>
    </StopTrigger>"""

    if "<StopTrigger/>" in content:
        content = content.replace("<StopTrigger/>", stop_block)
        with open(xosc_path, "w", encoding="utf-8") as f:
            f.write(content)
    elif "<StopTrigger>" in content and "SimulationTimeCondition" not in content:
        content = re.sub(r"<StopTrigger>.*?</StopTrigger>", stop_block, content, flags=re.DOTALL)
        with open(xosc_path, "w", encoding="utf-8") as f:
            f.write(content)

def run_esmini_simulation(xosc_path: str = "/tmp/adas/sample_fixed.xosc") -> Dict[str, Any]:
    """Executes OpenSCENARIO file via esmini inside Docker."""
    
    if not os.path.exists(xosc_path):
        return {
            "success": False,
            "exit_code": -1,
            "logs": f"Error: File '{xosc_path}' does not exist on host disk."
        }

    # 1. Automatically inject a 10s StopTrigger if missing/empty
    ensure_stop_condition(xosc_path, max_seconds=10.0)

    # 2. Resolve docker binary location
    docker_bin = shutil.which("docker") or "/usr/local/bin/docker"

    # 3. Clean CLI command (removed invalid --end_time)
    docker_cmd = (
        f"{docker_bin} run --rm --platform linux/amd64 "
        f"-v /tmp/adas:/tmp/adas "
        f"esmini-runner "
        f"--osc {xosc_path} --headless --fixed_timestep 0.05 --log_level info"
    )

    try:
        result = subprocess.run(
            docker_cmd,
            shell=True,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=20
        )
        
        output_log = (result.stdout + "\n" + result.stderr).strip()
     
    
        print("\n=== DOCKER ESMINI SIMULATION LOGS ===")
        print(output_log)
        print("=====================================\n")

        if not output_log:
            output_log = f"Process finished with exit code {result.returncode}"

        return {
            "success": result.returncode == 0,
            "exit_code": result.returncode,
            "logs": output_log[-1000:]
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "exit_code": -1, "logs": "Simulation timed out after 20 seconds."}
    except Exception as e:
        return {"success": False, "exit_code": -1, "logs": f"Execution exception: {str(e)}"}