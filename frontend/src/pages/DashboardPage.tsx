import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { ListTodo, CheckCircle, AlertCircle, Plus } from 'lucide-react';
import Card from '../components/Card';
import Badge from '../components/Badge';
import Button from '../components/Button';
import Header from '../components/Header';
import Spinner from '../components/Spinner';
import EmptyState from '../components/EmptyState';
import { createTask, getTasks } from '../services/taskService';
import type { TaskInfo, TaskMode } from '../types/api';
import { statusConfig, modeLabel } from '../constants/taskStatus';

export default function DashboardPage() {
  const navigate = useNavigate();
  const [tasks, setTasks] = useState<TaskInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [urls, setUrls] = useState('');
  const [mode, setMode] = useState<TaskMode>('basic');

  const stats = {
    total: tasks.length,
    success: tasks.filter((t) => t.status === 'completed').length,
    failed: tasks.filter((t) => t.status === 'failed').length,
  };

  const recentTasks = tasks.slice(0, 10);

  const fetchTasks = useCallback(async () => {
    try {
      setLoading(true);
      const res = await getTasks(1, 1000);
      setTasks(res.data.items ?? []);
    } catch {
      toast.error('加载任务列表失败');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTasks();
  }, [fetchTasks]);

  const handleSubmit = async () => {
    const urlList = urls
      .split('\n')
      .map((u) => u.trim())
      .filter((u) => u.length > 0);

    if (urlList.length === 0) {
      toast.error('请输入至少一个视频链接');
      return;
    }

    try {
      setSubmitting(true);
      const res = await createTask({ urls: urlList, mode });
      const firstTask = res.data[0];
      toast.success('任务创建成功');
      navigate(`/tasks/${firstTask.task_id}`);
    } catch {
      toast.error('任务创建失败');
    } finally {
      setSubmitting(false);
    }
  };

  const formatTime = (isoStr: string) => {
    const d = new Date(isoStr);
    const now = new Date();
    const diff = now.getTime() - d.getTime();
    const minutes = Math.floor(diff / 60000);
    if (minutes < 1) return '刚刚';
    if (minutes < 60) return `${minutes} 分钟前`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours} 小时前`;
    const days = Math.floor(hours / 24);
    if (days < 30) return `${days} 天前`;
    return d.toLocaleDateString('zh-CN');
  };

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <Spinner />
      </div>
    );
  }

  return (
    <div>
      <Header title="仪表盘" subtitle="管理您的 B站视频笔记任务" />

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
        <Card>
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-blue-50">
              <ListTodo className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-text-secondary">总任务数</p>
              <p className="text-2xl font-bold text-text">{stats.total}</p>
            </div>
          </div>
        </Card>
        <Card>
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-green-50">
              <CheckCircle className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-text-secondary">成功数</p>
              <p className="text-2xl font-bold text-text">{stats.success}</p>
            </div>
          </div>
        </Card>
        <Card>
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-red-50">
              <AlertCircle className="w-5 h-5 text-red-600" />
            </div>
            <div>
              <p className="text-sm text-text-secondary">失败数</p>
              <p className="text-2xl font-bold text-text">{stats.failed}</p>
            </div>
          </div>
        </Card>
      </div>

      <Card className="border-2 border-dashed border-gray-300 mb-8">
        <div className="flex items-center gap-2 mb-4">
          <Plus className="w-5 h-5 text-text-secondary" />
          <h2 className="text-lg font-semibold text-text">快速提交</h2>
        </div>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-text mb-1.5">
              视频链接（每行一个）
            </label>
            <textarea
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent resize-y min-h-[100px]"
              placeholder="https://www.bilibili.com/video/BV1xx411c7mD&#10;https://www.bilibili.com/video/BV1es4y1A7bq"
              value={urls}
              onChange={(e) => setUrls(e.target.value)}
            />
          </div>
          <div className="flex items-end gap-3">
            <div>
              <label className="block text-sm font-medium text-text mb-1.5">
                处理模式
              </label>
              <select
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent bg-white"
                value={mode}
                onChange={(e) => setMode(e.target.value as TaskMode)}
              >
                <option value="basic">基础模式</option>
                <option value="with_images">配图模式</option>
              </select>
            </div>
            <Button onClick={handleSubmit} loading={submitting}>
              提交任务
            </Button>
          </div>
        </div>
      </Card>

      <div>
        <h2 className="text-lg font-semibold text-text mb-4">最近任务</h2>
        {recentTasks.length === 0 ? (
          <Card>
            <EmptyState
              icon={<ListTodo className="w-12 h-12" />}
              title="暂无任务"
              description="在上方快速提交区域输入 B站视频链接，开始您的第一个笔记任务"
            />
          </Card>
        ) : (
          <Card className="p-0 overflow-hidden">
            <div className="divide-y divide-gray-100">
              {recentTasks.map((task) => {
                const sc = statusConfig[task.status];
                return (
                  <div
                    key={task.task_id}
                    className="flex items-center justify-between px-6 py-4 hover:bg-gray-50 cursor-pointer transition-colors"
                    onClick={() => navigate(`/tasks/${task.task_id}`)}
                  >
                    <div className="flex-1 min-w-0 mr-4">
                      <p className="text-sm font-medium text-text truncate">
                        {task.title || task.url}
                      </p>
                    </div>
                    <div className="flex items-center gap-3 shrink-0">
                      <Badge variant="default">{modeLabel[task.mode as TaskMode] ?? task.mode}</Badge>
                      <Badge variant={sc.variant}>{sc.label}</Badge>
                      <span className="text-xs text-text-secondary w-20 text-right">
                        {formatTime(task.created_at)}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}
