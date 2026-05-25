import api from './api';
import type { ApiResponse, VideoMetadata } from '../types/api';

// Output endpoints now return ApiResponse-wrapped JSON (not raw text),
// so res.data.data is the actual content.

export async function getSummary(taskId: string): Promise<string> {
  const res = await api.get<ApiResponse<string>>(`/outputs/${taskId}/summary`);
  return res.data.data ?? '';
}

export async function getMindmapMd(taskId: string): Promise<string> {
  const res = await api.get<ApiResponse<string>>(`/outputs/${taskId}/mindmap`);
  return res.data.data ?? '';
}

export async function getMindmapHtml(taskId: string): Promise<string> {
  const res = await api.get<ApiResponse<string>>(`/outputs/${taskId}/mindmap.html`);
  return res.data.data ?? '';
}

export async function getTranscript(taskId: string): Promise<string> {
  const res = await api.get<ApiResponse<string>>(`/outputs/${taskId}/transcript`);
  return res.data.data ?? '';
}

export async function getTranscriptPunct(taskId: string): Promise<string> {
  const res = await api.get<ApiResponse<string>>(`/outputs/${taskId}/transcript-punct`);
  return res.data.data ?? '';
}

export async function getTranscriptImages(taskId: string): Promise<string> {
  const res = await api.get<ApiResponse<string>>(`/outputs/${taskId}/transcript-images`);
  return res.data.data ?? '';
}

export async function getMetadata(taskId: string): Promise<VideoMetadata> {
  const res = await api.get<ApiResponse<VideoMetadata>>(`/outputs/${taskId}/metadata`);
  return res.data.data ?? ({} as VideoMetadata);
}
