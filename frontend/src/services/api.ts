import axios from 'axios';
import { ValidationResponse } from '../types';

const API_BASE_URL = 'http://localhost:8000/api/v1';

export const validateScenario = async (
  scenarioFile: File,
  telemetryFile: File
): Promise<ValidationResponse> => {
  const formData = new FormData();
  formData.append('scenario', scenarioFile);
  formData.append('telemetry', telemetryFile);

  const response = await axios.post<ValidationResponse>(
    `${API_BASE_URL}/validate`,
    formData,
   
  );

  return response.data;
};