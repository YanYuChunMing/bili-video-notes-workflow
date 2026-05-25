import type { TaskStatus, TaskMode } from '../types/api';

export const statusConfig: Record<TaskStatus, { label: string; variant: 'default' | 'success' | 'warning' | 'error' }> = {
  pending: { label: '等待中', variant: 'default' },
  downloading: { label: '下载中', variant: 'warning' },
  transcribing: { label: '转录中', variant: 'warning' },
  cleaning: { label: 'AI 标点整理', variant: 'warning' },
  summarizing: { label: 'AI 生成摘要', variant: 'warning' },
  mindmap: { label: 'AI 生成导图', variant: 'warning' },
  screenshot: { label: '智能截图', variant: 'warning' },
  completed: { label: '已完成', variant: 'success' },
  failed: { label: '失败', variant: 'error' },
};

export const modeLabel: Record<TaskMode, string> = {
  basic: '基础',
  with_images: '配图',
};
