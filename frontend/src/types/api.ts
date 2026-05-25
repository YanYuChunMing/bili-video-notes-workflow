// Auto-generated from the backend OpenAPI schema via openapi-typescript.
// Regenerate with: npm run generate-types
// The generated file is api.generated.ts — this file re-exports with friendly names.

import type { components } from './api.generated';

// --- Schema types ---
export type TaskMode = components['schemas']['TaskMode'];
export type TaskStatus = components['schemas']['TaskStatus'];
export type TaskInfo = components['schemas']['TaskInfo'];
export type TaskCreateRequest = components['schemas']['TaskCreateRequest'];
export type ConfigUpdateRequest = components['schemas']['ConfigUpdateRequest'];
export type ConfigDisplay = components['schemas']['ConfigDisplay'];
export type WhisperConfig = components['schemas']['WhisperConfig'];
export type DeepseekConfig = components['schemas']['DeepseekConfig'];
export type ScreenshotConfig = components['schemas']['ScreenshotConfig'];
export type ProjectConfig = components['schemas']['ProjectConfig'];
export type ApiKeyStatus = components['schemas']['ApiKeyStatus'];
export type VideoMetadata = components['schemas']['VideoMetadata'];

// Legacy alias: the config GET endpoint returns ConfigDisplay
export type AppConfig = ConfigDisplay;

// --- ApiResponse — hand-written generic wrapper ---
// The generated ApiResponse has `data?: unknown` because openapi-typescript
// can't expand Pydantic generics. We wrap it for consumer convenience.
export interface ApiResponse<T = unknown> {
  code: number;
  message: string;
  data: T;
}

// --- Paginated data (hand-written, no backend Pydantic model for this) ---
export interface PaginatedData<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

// --- WebSocket messages (not in OpenAPI, protocol-level) ---
export interface WsProgressMessage {
  type: 'progress' | 'error' | 'complete';
  task_id: string;
  stage?: string;
  message: string;
  progress: number;
  timestamp: string;
  status?: string;
}
