import pandas as pd
from typing import Dict, Any

def extract_anomaly_window(csv_path: str, ttc_threshold: float = 1.5) -> Dict[str, Any]:
    try:
        df = pd.read_csv(csv_path)
        anomalies = df[df['ttc'] < ttc_threshold]
        
        if anomalies.empty:
            return {"has_anomalies": False, "anomalies_summary": []}

        summary = anomalies[['frame', 'timestamp', 'ego_speed', 'target_distance', 'ttc']].head(15).to_dict(orient="records")
        return {
            "has_anomalies": True,
            "min_ttc": float(anomalies['ttc'].min()),
            "anomaly_count": len(anomalies),
            "sample_frames": summary
        }
    except Exception as e:
        return {"has_anomalies": False, "error": str(e)}
