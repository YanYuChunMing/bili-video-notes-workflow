import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { Trash2, Eye, ListTodo, ChevronLeft, ChevronRight } from 'lucide-react';
import Card from '../components/Card';
import Badge from '../components/Badge';
import Button from '../components/Button';
import Header from '../components/Header';
import Spinner from '../components/Spinner';
import EmptyState from '../components/EmptyState';
import { getTasks, deleteTask } from '../services/taskService';
import type { TaskInfo } from '../types/api';
import { statusConfig } from '../constants/taskStatus';

const PAGE_SIZE = 20;

const tabs = [
  { key: 'all', label: '全部', filter: () => true },
  { key: 'completed', label: '已完成', filter: (t: TaskInfo) => t.status === 'completed' },
  { key: 'failed', label: '失败', filter: (t: TaskInfo) => t.status === 'failed' },
  { key: 'processing', label: '处理中', filter: (t: TaskInfo) => !['completed', 'failed'].includes(t.status) },
];

function formatTime(dateStr: string): string {
  if (!dateStr) return '-';
  const d = new Date(dateStr);
  return d.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export default function TaskListPage() {
  const navigate = useNavigate();
  const [tasks, setTasks] = useState<TaskInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('all');
  const [page, setPage] = useState(1);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<TaskInfo | null>(null);

  useEffect(() => {
    loadTasks();
  }, []);

  async function loadTasks() {
    setLoading(true);
    try {
      const res = await getTasks(1, 100);
      if (res.code === 200 || res.code === 0) {
        setTasks(res.data.items);
      }
    } catch {
      toast.error('加载任务列表失败');
    } finally {
      setLoading(false);
    }
  }

  const filteredTasks = tasks.filter((t) => {
    const tab = tabs.find((tb) => tb.key === activeTab);
    return tab ? tab.filter(t) : true;
  });

  const totalPages = Math.max(1, Math.ceil(filteredTasks.length / PAGE_SIZE));
  const safePage = Math.min(page, totalPages);

  useEffect(() => {
    if (page > totalPages) {
      setPage(totalPages);
    }
  }, [filteredTasks.length, totalPages]);

  const pagedTasks = filteredTasks.slice((safePage - 1) * PAGE_SIZE, safePage * PAGE_SIZE);

  function handleRowClick(task: TaskInfo) {
    navigate(`/tasks/${task.task_id}`);
  }

  function openDeleteModal(task: TaskInfo, e: React.MouseEvent) {
    e.stopPropagation();
    setDeleteTarget(task);
  }

  function closeDeleteModal() {
    setDeleteTarget(null);
    setDeletingId(null);
  }

  async function confirmDelete() {
    if (!deleteTarget) return;
    setDeletingId(deleteTarget.task_id);
    try {
      await deleteTask(deleteTarget.task_id);
      setTasks((prev) => prev.filter((t) => t.task_id !== deleteTarget.task_id));
      toast.success('任务已删除');
    } catch {
      toast.error('删除失败');
    } finally {
      closeDeleteModal();
    }
  }

  function getPaginationRange(): (number | string)[] {
    const range: (number | string)[] = [];
    const delta = 2;
    for (let i = 1; i <= totalPages; i++) {
      if (i === 1 || i === totalPages || (i >= safePage - delta && i <= safePage + delta)) {
        range.push(i);
      } else if (range[range.length - 1] !== '...') {
        range.push('...');
      }
    }
    return range;
  }

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto">
        <Header title="任务列表" subtitle="管理所有视频处理任务" />
        <Spinner />
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto">
      <Header title="任务列表" subtitle="管理所有视频处理任务" />

      <div className="flex gap-1 mb-6 border-b border-gray-200">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => { setActiveTab(tab.key); setPage(1); }}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab.key
                ? 'border-primary text-primary'
                : 'border-transparent text-text-secondary hover:text-text hover:border-gray-300'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {filteredTasks.length === 0 ? (
        <Card>
          <EmptyState
            icon={<ListTodo size={48} />}
            title="暂无任务"
            description={
              activeTab === 'all'
                ? '还没有创建任何任务，去首页添加视频链接开始吧'
                : '当前分类下没有任务'
            }
          />
        </Card>
      ) : (
        <>
          <Card className="p-0 overflow-hidden">
            <div className="hidden md:block overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-100">
                    <th className="text-left px-6 py-3 text-xs font-medium text-text-secondary uppercase tracking-wider w-12">#</th>
                    <th className="text-left px-6 py-3 text-xs font-medium text-text-secondary uppercase tracking-wider">标题</th>
                    <th className="text-left px-6 py-3 text-xs font-medium text-text-secondary uppercase tracking-wider w-20">模式</th>
                    <th className="text-left px-6 py-3 text-xs font-medium text-text-secondary uppercase tracking-wider w-24">状态</th>
                    <th className="text-left px-6 py-3 text-xs font-medium text-text-secondary uppercase tracking-wider w-36">处理时间</th>
                    <th className="text-left px-6 py-3 text-xs font-medium text-text-secondary uppercase tracking-wider w-28">操作</th>
                  </tr>
                </thead>
                <tbody>
                  {pagedTasks.map((task, idx) => (
                    <tr
                      key={task.task_id}
                      onClick={() => handleRowClick(task)}
                      className="border-b border-gray-50 hover:bg-gray-50 cursor-pointer transition-colors"
                    >
                      <td className="px-6 py-4 text-sm text-text-secondary">{(safePage - 1) * PAGE_SIZE + idx + 1}</td>
                      <td className="px-6 py-4">
                        <p className="text-sm font-medium text-text line-clamp-1">{task.title || '无标题'}</p>
                      </td>
                      <td className="px-6 py-4">
                        <span className="text-xs text-text-secondary">{task.mode === 'with_images' ? '图文' : '基础'}</span>
                      </td>
                      <td className="px-6 py-4">
                        <Badge variant={statusConfig[task.status]?.variant ?? 'default'}>
                          {statusConfig[task.status]?.label ?? task.status}
                        </Badge>
                      </td>
                      <td className="px-6 py-4 text-sm text-text-secondary whitespace-nowrap">
                        {formatTime(task.created_at)}
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                          <button
                            onClick={() => handleRowClick(task)}
                            className="p-1.5 rounded hover:bg-gray-100 text-text-secondary hover:text-primary transition-colors"
                            title="查看详情"
                          >
                            <Eye size={16} />
                          </button>
                          <button
                            onClick={(e) => openDeleteModal(task, e)}
                            className="p-1.5 rounded hover:bg-red-50 text-text-secondary hover:text-red-500 transition-colors"
                            title="删除任务"
                          >
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="md:hidden divide-y divide-gray-100">
              {pagedTasks.map((task, idx) => (
                <div
                  key={task.task_id}
                  onClick={() => handleRowClick(task)}
                  className="p-4 hover:bg-gray-50 cursor-pointer transition-colors"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-text line-clamp-2">{task.title || '无标题'}</p>
                      <div className="flex items-center gap-2 mt-2">
                        <Badge variant={statusConfig[task.status]?.variant ?? 'default'}>
                          {statusConfig[task.status]?.label ?? task.status}
                        </Badge>
                        <span className="text-xs text-text-secondary">{task.mode === 'with_images' ? '图文' : '基础'}</span>
                      </div>
                      <p className="text-xs text-text-secondary mt-2">{formatTime(task.created_at)}</p>
                    </div>
                    <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
                      <button
                        onClick={() => handleRowClick(task)}
                        className="p-1.5 rounded hover:bg-gray-100 text-text-secondary hover:text-primary transition-colors"
                      >
                        <Eye size={16} />
                      </button>
                      <button
                        onClick={(e) => openDeleteModal(task, e)}
                        className="p-1.5 rounded hover:bg-red-50 text-text-secondary hover:text-red-500 transition-colors"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </div>
                  <p className="text-xs text-text-secondary mt-1">#{(safePage - 1) * PAGE_SIZE + idx + 1}</p>
                </div>
              ))}
            </div>
          </Card>

          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-1 mt-6">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={safePage <= 1}
                className="p-2 rounded-lg border border-gray-200 text-text-secondary hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronLeft size={16} />
              </button>
              {getPaginationRange().map((item, i) =>
                item === '...' ? (
                  <span key={`dots-${i}`} className="px-2 text-text-secondary text-sm">...</span>
                ) : (
                  <button
                    key={item}
                    onClick={() => setPage(item as number)}
                    className={`w-9 h-9 rounded-lg text-sm font-medium transition-colors ${
                      safePage === item
                        ? 'bg-primary text-white'
                        : 'text-text-secondary hover:bg-gray-100'
                    }`}
                  >
                    {item}
                  </button>
                )
              )}
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={safePage >= totalPages}
                className="p-2 rounded-lg border border-gray-200 text-text-secondary hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronRight size={16} />
              </button>
            </div>
          )}
        </>
      )}

      {deleteTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30" onClick={closeDeleteModal}>
          <div onClick={(e) => e.stopPropagation()}>
            <Card className="w-full max-w-sm mx-4">
              <h3 className="text-lg font-semibold text-text mb-2">删除任务</h3>
              <p className="text-sm text-text-secondary mb-6">
                确定要删除此任务吗？此操作不可撤销。
              </p>
              <p className="text-sm font-medium text-text mb-6 line-clamp-2 bg-gray-50 rounded-lg p-3">
                {deleteTarget.title || '无标题'}
              </p>
              <div className="flex justify-end gap-3">
                <Button variant="secondary" onClick={closeDeleteModal} disabled={deletingId === deleteTarget.task_id}>
                  取消
                </Button>
                <Button
                  variant="danger"
                  onClick={confirmDelete}
                  loading={deletingId === deleteTarget.task_id}
                >
                  确认删除
                </Button>
              </div>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
