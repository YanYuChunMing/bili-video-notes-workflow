import api from './api';
import type { ApiResponse, PaginatedData, TaskInfo, TaskCreateRequest } from '../types/api';

export async function createTask(data: TaskCreateRequest): Promise<ApiResponse<TaskInfo[]>> {
  const res = await api.post<ApiResponse<TaskInfo[]>>('/tasks', data);
  return res.data;
}

export async function getTasks(page = 1, pageSize = 20): Promise<ApiResponse<PaginatedData<TaskInfo>>> {
  const res = await api.get('/tasks', { params: { page, page_size: pageSize } });
  return res.data;
}

export async function getTask(taskId: string): Promise<ApiResponse<TaskInfo>> {
  const res = await api.get(`/tasks/${taskId}`);
  return res.data;
}

export async function deleteTask(taskId: string): Promise<ApiResponse<null>> {
  const res = await api.delete(`/tasks/${taskId}`);
  return res.data;
}
