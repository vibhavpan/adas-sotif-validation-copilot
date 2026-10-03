export interface TelemetryAnomaly {
  frame: number;
  timestamp: number;
  ego_speed: number;
  target_distance: number;
  ttc: number;
}

export interface ValidationResponse {
  status: 'success' | 'error';
  diagnosis: string;
  patch_file: string;
  original_xml?: string;
  patched_xml?: string;
  simulation_result: {
    success: boolean;
    exit_code: number;
    logs: string;
  };
  retries_taken: number;
}