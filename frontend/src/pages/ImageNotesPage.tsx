import Button from '../components/Button'
import Spinner from '../components/Spinner'
import EmptyState from '../components/EmptyState'
import { getTranscriptImages } from '../services/outputService'
import { getTask } from '../services/taskService'
import { useParams, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { ArrowLeft, Image } from 'lucide-react'
import { useAsyncEffect } from '../hooks/useAsyncEffect'

export default function ImageNotesPage() {
  const { taskId } = useParams<{ taskId: string }>()
  const navigate = useNavigate()
  const [markdown, setMarkdown] = useState<string | null>(null)
  const [taskTitle, setTaskTitle] = useState('')
  const [emptyReason, setEmptyReason] = useState<string | null>(null)

  const { loading, error } = useAsyncEffect(async (cancelled) => {
    if (!taskId) return
    const id = taskId

    const [markdownContent, taskRes] = await Promise.all([
      getTranscriptImages(id),
      getTask(id),
    ])
    if (cancelled()) return

    if (taskRes.data?.title) {
      setTaskTitle(taskRes.data.title)
    }
    if (!markdownContent) {
      setEmptyReason('图文笔记数据为空')
      return
    }
    setMarkdown(markdownContent)
  }, [taskId])

  const headerBar = (
    <div className="flex items-center gap-3 px-6 py-4 border-b border-gray-100">
      <Button variant="ghost" size="sm" onClick={() => navigate(-1)}>
        <ArrowLeft size={18} />
      </Button>
      <Image size={20} className="text-primary" />
      <h1 className="text-lg font-semibold text-text">图文笔记{taskTitle ? ` - ${taskTitle}` : ''}</h1>
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

  if (error || emptyReason || !markdown) {
    return (
      <div className="flex flex-col h-full">
        {headerBar}
        <div className="flex-1 flex items-center justify-center">
          <EmptyState
            icon={<Image size={48} />}
            title="暂无图文笔记"
            description={error || emptyReason || '任务尚未生成图文笔记'}
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
      <div className="flex-1 overflow-y-auto px-6 py-6">
        <div className="max-w-4xl mx-auto prose prose-slate">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              img: ({ src, alt }) => {
                if (!src) return null
                const imageSrc = src.startsWith('http') ? src : `/media/${taskId}/${src.replace(/^\.\.\//, '')}`
                return <img src={imageSrc} alt={alt || ''} loading="lazy" className="max-w-full h-auto rounded-lg my-4 shadow-md" />
              },
            }}
          >
            {markdown}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  )
}
