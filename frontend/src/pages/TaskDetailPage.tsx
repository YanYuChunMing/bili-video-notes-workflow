import Card from '../components/Card';
import Badge from '../components/Badge';
import Button from '../components/Button';
import Header from '../components/Header';
import Spinner from '../components/Spinner';
import EmptyState from '../components/EmptyState';
import { getTask } from '../services/taskService';
import { getMetadata } from '../services/outputService';
import { useWebSocket } from '../hooks/useWebSocket';
import type { TaskInfo, TaskStatus, VideoMetadata, WsProgressMessage } from '../types/api';
import { useParams, useNavigate } from 'react-router-dom';
import { useEffect, useState, useCallback } from 'react';
import {
  ArrowLeft,
  FileText,
  GitBranch,
  BookOpen,
  Image,
  ExternalLink,
  Clock,
  User,
  Calendar,
  Link as LinkIcon,
} from 'lucide-react';

import { statusConfig } from '../constants/taskStatus';

const stages = [
  { key: 'downloading', label: '下载音频' },
  { key: 'transcribing', label: '语音转录' },
  { key: 'cleaning', label: 'AI 标点整理' },
  { key: 'summarizing', label: 'AI 生成摘要' },
  { key: 'mindmap', label: 'AI 思维导图' },
  { key: 'screenshot', label: '智能截图' },
];

const outputFiles = [
  { path: 'summary', label: '学习笔记', icon: BookOpen, desc: 'AI 提炼的知识要点', color: 'text-blue-500' },
  { path: 'mindmap.html', label: '思维导图', icon: GitBranch, desc: '可视化知识结构', color: 'text-purple-500' },
  { path: 'transcript', label: '纯文字稿', icon: FileText, desc: '视频逐字稿', color: 'text-gray-500' },
  { path: 'transcript-punct', label: '带标点文字稿', icon: FileText, desc: 'AI 整理后的文字稿', color: 'text-green-500' },
  { path: 'transcript-images', label: '图文笔记', icon: Image, desc: '带截图的笔记', color: 'text-orange-500' },
];

function formatDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  if (h > 0) {
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  }
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr);
  return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日`;
}

function formatCompletedAt(dateStr: string): string {
  const d = new Date(dateStr);
  return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日 ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}:${String(d.getSeconds()).padStart(2, '0')}`;
}

function getCurrentStageIndex(status: string): number {
  if (status === 'completed') return stages.length;
  if (status === 'failed' || status === 'pending') return -1;
  const idx = stages.findIndex((s) => s.key === status);
  return idx >= 0 ? idx : -1;
}

function getFileNavigatePath(taskId: string, path: string): string {
  switch (path) {
    case 'mindmap.html':
      return `/notes/${taskId}/mindmap`;
    case 'transcript-images':
      return `/notes/${taskId}/images`;
    default:
      return `/notes/${taskId}`;
  }
}

export default function TaskDetailPage() {
  const { taskId } = useParams<{ taskId: string }>();
  const navigate = useNavigate();

  const [task, setTask] = useState<TaskInfo | null>(null);
  const [metadata, setMetadata] = useState<VideoMetadata | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadTask = useCallback(async () => {
    if (!taskId) return;
    try {
      setLoading(true);
      setError(null);
      const res = await getTask(taskId);
      setTask(res.data);
    } catch {
      setError('加载任务信息失败');
    } finally {
      setLoading(false);
    }
  }, [taskId]);

  const loadMetadata = useCallback(async () => {
    if (!taskId) return;
    try {
      const data = await getMetadata(taskId);
      setMetadata(data);
    } catch {
      // metadata is optional, ignore errors
    }
  }, [taskId]);

  const handleWsMessage = useCallback((msg: WsProgressMessage) => {
    setTask((prev) => {
      if (!prev) return prev;
      if (msg.task_id !== prev.task_id) return prev;
      return {
        ...prev,
        status: msg.stage as TaskStatus,
        progress: msg.progress,
        stage_message: msg.message,
      };
    });
  }, []);

  const { isConnected } = useWebSocket({
    taskId: task && task.status !== 'completed' && task.status !== 'failed' ? task.task_id : null,
    onMessage: handleWsMessage,
    enabled: true,
  });

  useEffect(() => {
    loadTask();
  }, [loadTask]);

  useEffect(() => {
    loadMetadata();
  }, [loadMetadata]);

  const handleBack = () => {
    navigate('/tasks');
  };

  const handleOutputClick = (path: string) => {
    if (!taskId) return;
    navigate(getFileNavigatePath(taskId, path));
  };

  const handleOpenOriginal = () => {
    if (metadata?.webpage_url) {
      window.open(metadata.webpage_url, '_blank');
    } else if (task?.url) {
      window.open(task.url, '_blank');
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <Spinner />
      </div>
    );
  }

  if (error || !task) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <EmptyState
          title="加载失败"
          description={error || '任务不存在'}
          action={
            <Button variant="secondary" onClick={handleBack}>
              <ArrowLeft className="w-4 h-4" />
              返回任务列表
            </Button>
          }
        />
      </div>
    );
  }

  const currentStageIndex = getCurrentStageIndex(task.status);
  const isCompleted = task.status === 'completed';
  const isFailed = task.status === 'failed';
  const isProcessing = !isCompleted && !isFailed && task.status !== 'pending';
  const progressPercent = task.progress != null ? Math.round(task.progress * 100) : 0;

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <Header
        title="任务详情"
        action={
          <Button variant="ghost" size="sm" onClick={handleBack}>
            <ArrowLeft className="w-4 h-4" />
            返回
          </Button>
        }
      />

      {isFailed && (
        <Card className="mb-6 border-l-4 border-red-500 bg-red-50">
          <div className="flex items-start gap-3">
            <div className="text-red-500 font-semibold">任务处理失败</div>
            <p className="text-sm text-red-600 mt-1">{task.error_message || '未知错误'}</p>
          </div>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <div className="lg:col-span-2">
          <Card>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-text">视频信息</h2>
              <Badge variant={statusConfig[task.status].variant}>
                {statusConfig[task.status].label}
              </Badge>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="flex items-start gap-2">
                <FileText className="w-4 h-4 text-text-secondary mt-0.5 shrink-0" />
                <div>
                  <p className="text-xs text-text-secondary mb-0.5">标题</p>
                  <p className="text-sm text-text font-medium line-clamp-2">
                    {metadata?.title || task.title || '无标题'}
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-2">
                <User className="w-4 h-4 text-text-secondary mt-0.5 shrink-0" />
                <div>
                  <p className="text-xs text-text-secondary mb-0.5">UP 主</p>
                  <p className="text-sm text-text">{metadata?.uploader || '未知'}</p>
                </div>
              </div>

              <div className="flex items-start gap-2">
                <Clock className="w-4 h-4 text-text-secondary mt-0.5 shrink-0" />
                <div>
                  <p className="text-xs text-text-secondary mb-0.5">时长</p>
                  <p className="text-sm text-text">
                    {metadata?.duration != null ? formatDuration(metadata.duration) : '未知'}
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-2">
                <Calendar className="w-4 h-4 text-text-secondary mt-0.5 shrink-0" />
                <div>
                  <p className="text-xs text-text-secondary mb-0.5">上传日期</p>
                  <p className="text-sm text-text">
                    {metadata?.upload_date ? formatDate(metadata.upload_date) : '未知'}
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-2 sm:col-span-2">
                <LinkIcon className="w-4 h-4 text-text-secondary mt-0.5 shrink-0" />
                <div className="min-w-0 flex-1">
                  <p className="text-xs text-text-secondary mb-0.5">原始链接</p>
                  <button
                    onClick={handleOpenOriginal}
                    className="text-sm text-primary hover:text-primary-dark truncate block max-w-full text-left"
                  >
                    {metadata?.webpage_url || task.url}
                  </button>
                </div>
              </div>
            </div>
          </Card>
        </div>

        <Card>
          <h3 className="text-sm font-medium text-text mb-3">任务概览</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-text-secondary">任务 ID</span>
              <span className="text-text font-mono text-xs truncate ml-2 max-w-[180px]">{task.task_id}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-secondary">处理模式</span>
              <span className="text-text">{task.mode === 'with_images' ? '图文笔记' : '基础笔记'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-secondary">创建时间</span>
              <span className="text-text">{task.created_at ? formatCompletedAt(task.created_at) : '-'}</span>
            </div>
            {isCompleted && task.completed_at && (
              <div className="flex justify-between">
                <span className="text-text-secondary">完成时间</span>
                <span className="text-text">{formatCompletedAt(task.completed_at)}</span>
              </div>
            )}
            {task.stage_message && (
              <div className="flex justify-between">
                <span className="text-text-secondary">状态信息</span>
                <span className="text-text truncate ml-2 max-w-[180px]">{task.stage_message}</span>
              </div>
            )}
          </div>
          {isConnected && (
            <div className="mt-3 flex items-center gap-1.5 text-xs text-green-600">
              <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
              实时连接中
            </div>
          )}
        </Card>
      </div>

      {isProcessing && (
        <Card className="mb-6">
          <h3 className="text-sm font-medium text-text mb-4">处理进度</h3>

          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-text-secondary">
              {stages[currentStageIndex]?.label || '处理中'}
            </span>
            <span className="text-sm font-semibold text-primary">{progressPercent}%</span>
          </div>

          <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-500 ease-out"
              style={{
                width: `${progressPercent}%`,
                background: 'linear-gradient(90deg, var(--tw-color-primary, #3b82f6), var(--tw-color-success, #22c55e))',
              }}
            />
          </div>

          <div className="mt-4 space-y-2">
            {stages.map((stage, idx) => {
              const isCurrentStage = idx === currentStageIndex;
              const isPastStage = idx < currentStageIndex;

              return (
                <div key={stage.key} className="flex items-center gap-2">
                  <div
                    className={`w-5 h-5 rounded-full flex items-center justify-center text-xs shrink-0 ${
                      isPastStage
                        ? 'bg-green-500 text-white'
                        : isCurrentStage
                          ? 'bg-primary text-white animate-pulse'
                          : 'bg-gray-200 text-gray-400'
                    }`}
                  >
                    {isPastStage ? '✓' : idx + 1}
                  </div>
                  <span
                    className={`text-sm ${
                      isPastStage
                        ? 'text-green-600'
                        : isCurrentStage
                          ? 'text-primary font-medium'
                          : 'text-gray-400'
                    }`}
                  >
                    {stage.label}
                  </span>
                </div>
              );
            })}
          </div>
        </Card>
      )}

      {isCompleted && (
        <Card>
          <h3 className="text-sm font-medium text-text mb-4">产物文件</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {outputFiles.map((file) => (
              <button
                key={file.path}
                onClick={() => handleOutputClick(file.path)}
                className="flex items-start gap-3 p-3 rounded-lg border border-gray-200 hover:border-primary hover:bg-primary/5 transition-colors text-left"
              >
                <file.icon className={`w-5 h-5 ${file.color} mt-0.5 shrink-0`} />
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-text">{file.label}</p>
                  <p className="text-xs text-text-secondary">{file.desc}</p>
                </div>
                <ExternalLink className="w-4 h-4 text-text-secondary shrink-0 mt-0.5" />
              </button>
            ))}

            {metadata?.webpage_url && (
              <button
                onClick={handleOpenOriginal}
                className="flex items-start gap-3 p-3 rounded-lg border border-gray-200 hover:border-primary hover:bg-primary/5 transition-colors text-left"
              >
                <ExternalLink className="w-5 h-5 text-indigo-500 mt-0.5 shrink-0" />
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-text">原始视频</p>
                  <p className="text-xs text-text-secondary">打开 B 站原视频</p>
                </div>
                <ExternalLink className="w-4 h-4 text-text-secondary shrink-0 mt-0.5" />
              </button>
            )}
          </div>
        </Card>
      )}

      {task.status === 'pending' && (
        <Card>
          <div className="flex flex-col items-center py-6 text-center">
            <Clock className="w-10 h-10 text-gray-300 mb-3" />
            <p className="text-sm text-text-secondary">任务正在排队等待处理...</p>
          </div>
        </Card>
      )}
    </div>
  );
}
