# backend/debug_sim.py
from app.sim.esmini_runner import run_esmini_simulation

print("Testing esmini runner against /tmp/adas/sample_fixed.xosc...")
result = run_esmini_simulation("/tmp/adas/sample_fixed.xosc")

print(f"\nExit Code: {result.get('exit_code')}")
print(f"Success: {result.get('success')}")
print("\n--- SIMULATION LOGS ---")
print(result.get("logs"))