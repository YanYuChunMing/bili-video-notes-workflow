import Button from '../components/Button'
import Spinner from '../components/Spinner'
import EmptyState from '../components/EmptyState'
import { getMindmapHtml } from '../services/outputService'
import { getTask } from '../services/taskService'
import { useParams, useNavigate } from 'react-router-dom'
import { useState, useRef } from 'react'
import { ArrowLeft, GitBranch } from 'lucide-react'
import { useAsyncEffect } from '../hooks/useAsyncEffect'

export default function MindmapPage() {
  const { taskId } = useParams<{ taskId: string }>()
  const navigate = useNavigate()
  const [html, setHtml] = useState<string | null>(null)
  const [taskTitle, setTaskTitle] = useState('')
  const [emptyReason, setEmptyReason] = useState<string | null>(null)
  const iframeRef = useRef<HTMLIFrameElement>(null)

  const { loading, error } = useAsyncEffect(async (cancelled) => {
    if (!taskId) return
    const id = taskId

    const [htmlContent, taskRes] = await Promise.all([
      getMindmapHtml(id),
      getTask(id),
    ])
    if (cancelled()) return

    if (taskRes.data?.title) {
      setTaskTitle(taskRes.data.title)
    }
    if (!htmlContent) {
      setEmptyReason('思维导图数据为空')
      return
    }
    setHtml(htmlContent)
  }, [taskId])

  const headerBar = (
    <div className="flex items-center gap-3 px-6 py-4 border-b border-gray-100">
      <Button variant="ghost" size="sm" onClick={() => navigate(-1)}>
        <ArrowLeft size={18} />
      </Button>
      <GitBranch size={20} className="text-primary" />
      <h1 className="text-lg font-semibold text-text">思维导图{taskTitle ? ` - ${taskTitle}` : ''}</h1>
    </div>
  )

  if (loading) {
    return (
      <div className="flex flex-col h-full">
        {headerBar}
        <div className="flex-1 flex items-center justify-center">
          <Spinner />
        </div>
      </div>
    )
  }

  if (error || emptyReason || !html) {
    return (
      <div className="flex flex-col h-full">
        {headerBar}
        <div className="flex-1 flex items-center justify-center">
          <EmptyState
            icon={<GitBranch size={48} />}
            title="暂无思维导图"
            description={error || emptyReason || '任务尚未生成思维导图'}
            action={
              <Button variant="secondary" onClick={() => navigate(-1)}>
                返回
              </Button>
            }
          />
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      {headerBar}
      <iframe
        ref={iframeRef}
        srcDoc={html}
        className="w-full border-none"
        style={{ minHeight: 'calc(100vh - 200px)' }}
        title="思维导图"
      />
    </div>
  )
}
