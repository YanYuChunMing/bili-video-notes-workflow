import api from './api';
import type { ApiResponse, AppConfig, ConfigUpdateRequest, ApiKeyStatus } from '../types/api';

export async function getConfig(): Promise<ApiResponse<AppConfig>> {
  const res = await api.get<ApiResponse<AppConfig>>('/config');
  return res.data;
}

export async function updateConfig(data: ConfigUpdateRequest): Promise<ApiResponse<null>> {
  const res = await api.put<ApiResponse<null>>('/config', data);
  return res.data;
}

export async function checkApiKey(): Promise<ApiResponse<ApiKeyStatus>> {
  const res = await api.get<ApiResponse<ApiKeyStatus>>('/config/check');
  return res.data;
}
