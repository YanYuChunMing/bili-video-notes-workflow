import { useEffect, useState, useMemo, useRef, useCallback } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeHighlight from 'rehype-highlight'
import { ArrowLeft, Type, Maximize2, Minimize2, GitBranch, Image, Clock, User, Calendar, List } from 'lucide-react'
import Card from '../components/Card'
import Badge from '../components/Badge'
import Button from '../components/Button'
import Spinner from '../components/Spinner'
import EmptyState from '../components/EmptyState'
import ErrorBoundary from '../components/ErrorBoundary'
import { getSummary, getTranscriptPunct, getMetadata } from '../services/outputService'
import { getTask } from '../services/taskService'
import type { TaskInfo, VideoMetadata } from '../types/api'

interface TocItem {
  id: string
  text: string
  level: number
}

function formatDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
  return `${m}:${String(s).padStart(2, '0')}`
}

function extractToc(markdown: string): TocItem[] {
  const headingRegex = /^(#{1,3})\s+(.+)$/gm
  const items: TocItem[] = []
  let match: RegExpExecArray | null
  while ((match = headingRegex.exec(markdown)) !== null) {
    const level = match[1].length
    const text = match[2].trim()
    const id = text
      .toLowerCase()
      .replace(/[^\w\u4e00-\u9fff\s-]/g, '')
      .replace(/\s+/g, '-')
    items.push({ id, text, level })
  }
  return items
}

function generateHeadingId(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^\w\u4e00-\u9fff\s-]/g, '')
    .replace(/\s+/g, '-')
}

export default function NotePage() {
  return (
    <ErrorBoundary>
      <NotePageInner />
    </ErrorBoundary>
  )
}

function NotePageInner() {
  const { taskId } = useParams<{ taskId: string }>()
  const navigate = useNavigate()

  const [task, setTask] = useState<TaskInfo | null>(null)
  const [content, setContent] = useState('')
  const [metadata, setMetadata] = useState<VideoMetadata | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [fontSize, setFontSize] = useState(16)
  const [fullWidth, setFullWidth] = useState(false)
  const [tocOpen, setTocOpen] = useState(false)
  const [progress, setProgress] = useState(0)
  const [activeTocId, setActiveTocId] = useState('')

  const contentRef = useRef<HTMLDivElement>(null)
  const headingObserverRef = useRef<IntersectionObserver | null>(null)

  useEffect(() => {
    if (!taskId) {
      setError('缺少任务 ID')
      setLoading(false)
      return
    }

    let cancelled = false

    async function loadData() {
      setLoading(true)
      setError(null)
      try {
        const [taskRes, summary, transcript, meta] = await Promise.allSettled([
          getTask(taskId!),
          getSummary(taskId!),
          getTranscriptPunct(taskId!),
          getMetadata(taskId!),
        ])

        if (cancelled) return

        if (taskRes.status === 'rejected') {
          setError('获取任务信息失败')
          setLoading(false)
          return
        }

        const taskData = taskRes.value.data as TaskInfo
        setTask(taskData)

        const summaryContent =
          summary.status === 'fulfilled' && summary.value ? summary.value : ''
        const transcriptContent =
          transcript.status === 'fulfilled' && transcript.value ? transcript.value : ''
        setContent(summaryContent || transcriptContent || '')

        if (meta.status === 'fulfilled') {
          setMetadata(meta.value)
        }
      } catch {
        if (!cancelled) setError('加载数据失败')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    loadData()
    return () => {
      cancelled = true
    }
  }, [taskId])

  const toc = useMemo(() => extractToc(content), [content])

  useEffect(() => {
    function handleScroll() {
      const scrollTop = window.scrollY
      const docHeight = document.documentElement.scrollHeight - window.innerHeight
      if (docHeight > 0) {
        setProgress(Math.min((scrollTop / docHeight) * 100, 100))
      }
    }

    window.addEventListener('scroll', handleScroll, { passive: true })
    handleScroll()
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  useEffect(() => {
    if (!contentRef.current || toc.length === 0) return

    if (headingObserverRef.current) {
      headingObserverRef.current.disconnect()
    }

    const headingElements = toc
      .map((item) => document.getElementById(item.id))
      .filter(Boolean) as HTMLElement[]

    if (headingElements.length === 0) return

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            setActiveTocId(entry.target.id)
          }
        }
      },
      { rootMargin: '-80px 0px -70% 0px', threshold: 0 }
    )

    headingElements.forEach((el) => observer.observe(el))
    headingObserverRef.current = observer

    return () => observer.disconnect()
  }, [toc, content])

  const handleFontSizeToggle = useCallback(() => {
    if (fontSize === 14) {
      setFontSize(16)
    } else if (fontSize === 16) {
      setFontSize(18)
    } else {
      setFontSize(14)
    }
  }, [fontSize])

  const scrollToHeading = useCallback((id: string) => {
    const el = document.getElementById(id)
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
    setTocOpen(false)
  }, [])

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16">
        <Spinner />
        <p className="text-center text-text-secondary mt-4">正在加载笔记...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16">
        <EmptyState
          title="加载失败"
          description={error}
          action={
            <Button variant="primary" onClick={() => window.location.reload()}>
              重试
            </Button>
          }
        />
      </div>
    )
  }

  if (!content) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16">
        <EmptyState
          title="暂无笔记内容"
          description="该任务的笔记内容为空，请确认任务已处理完成。"
          action={
            <Button variant="secondary" onClick={() => navigate('/tasks')}>
              返回任务列表
            </Button>
          }
        />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-bg">
      <div
        className="fixed top-0 left-0 right-0 z-50 h-[3px] bg-primary transition-all duration-150"
        style={{ width: `${progress}%` }}
      />

      <div className="sticky top-0 z-40 bg-bg/95 backdrop-blur-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between gap-3">
          <div className="flex items-center gap-3 min-w-0">
            <button
              onClick={() => navigate(-1)}
              className="flex-shrink-0 p-2 rounded-lg hover:bg-gray-200 text-text-secondary hover:text-text transition-colors"
              title="返回"
            >
              <ArrowLeft size={18} />
            </button>
            <h1 className="text-base font-semibold text-text truncate">
              {task?.title || '笔记'}
            </h1>
          </div>

          <div className="flex items-center gap-1 flex-shrink-0">
            <button
              onClick={handleFontSizeToggle}
              className="p-2 rounded-lg hover:bg-gray-200 text-text-secondary hover:text-text transition-colors flex items-center gap-1"
              title={`字体大小：${fontSize}px`}
            >
              <Type size={16} />
              <span className="text-xs font-medium w-7 text-center">{fontSize}px</span>
            </button>

            <button
              onClick={() => setFullWidth(!fullWidth)}
              className="p-2 rounded-lg hover:bg-gray-200 text-text-secondary hover:text-text transition-colors"
              title={fullWidth ? '标准宽度' : '全宽模式'}
            >
              {fullWidth ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
            </button>

            <Link
              to={`/notes/${taskId}/mindmap`}
              className="p-2 rounded-lg hover:bg-gray-200 text-text-secondary hover:text-text transition-colors"
              title="思维导图"
            >
              <GitBranch size={16} />
            </Link>

            <Link
              to={`/notes/${taskId}/images`}
              className="p-2 rounded-lg hover:bg-gray-200 text-text-secondary hover:text-text transition-colors"
              title="图文笔记"
            >
              <Image size={16} />
            </Link>

            <button
              onClick={() => setTocOpen(!tocOpen)}
              className="lg:hidden p-2 rounded-lg hover:bg-gray-200 text-text-secondary hover:text-text transition-colors relative"
              title="目录"
            >
              <List size={16} />
              {toc.length > 0 && (
                <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-primary text-white text-[10px] rounded-full flex items-center justify-center font-medium">
                  {toc.length}
                </span>
              )}
            </button>
          </div>
        </div>
      </div>

      {tocOpen && toc.length > 0 && (
        <div className="lg:hidden fixed inset-0 z-30 bg-black/30" onClick={() => setTocOpen(false)} />
      )}

      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className={`flex gap-8 ${fullWidth ? '' : 'max-w-5xl mx-auto'}`}>
          <div
            ref={contentRef}
            className="flex-1 min-w-0"
            style={{ fontSize: `${fontSize}px` }}
          >
            <Card className="prose max-w-none">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                rehypePlugins={[rehypeHighlight]}
                components={{
                  h1: ({ children, ...props }) => {
                    const text = extractTextContent(children)
                    const id = generateHeadingId(text)
                    return (
                      <h1
                        id={id}
                        className="text-2xl font-bold text-text mt-8 mb-4 pb-2 border-b border-gray-200 scroll-mt-20"
                        {...props}
                      >
                        {children}
                      </h1>
                    )
                  },
                  h2: ({ children, ...props }) => {
                    const text = extractTextContent(children)
                    const id = generateHeadingId(text)
                    return (
                      <h2
                        id={id}
                        className="text-xl font-semibold text-text mt-6 mb-3 scroll-mt-20"
                        {...props}
                      >
                        {children}
                      </h2>
                    )
                  },
                  h3: ({ children, ...props }) => {
                    const text = extractTextContent(children)
                    const id = generateHeadingId(text)
                    return (
                      <h3
                        id={id}
                        className="text-lg font-medium text-text mt-4 mb-2 scroll-mt-20"
                        {...props}
                      >
                        {children}
                      </h3>
                    )
                  },
                  p: ({ children, ...props }) => (
                    <p className="text-text leading-relaxed my-3" {...props}>
                      {children}
                    </p>
                  ),
                  ul: ({ children, ...props }) => (
                    <ul className="list-disc pl-6 my-3 space-y-1 text-text" {...props}>
                      {children}
                    </ul>
                  ),
                  ol: ({ children, ...props }) => (
                    <ol className="list-decimal pl-6 my-3 space-y-1 text-text" {...props}>
                      {children}
                    </ol>
                  ),
                  li: ({ children, ...props }) => (
                    <li className="leading-relaxed" {...props}>
                      {children}
                    </li>
                  ),
                  blockquote: ({ children, ...props }) => (
                    <blockquote
                      className="border-l-4 border-primary/40 pl-4 my-4 italic text-text-secondary bg-primary/5 py-2 pr-4 rounded-r"
                      {...props}
                    >
                      {children}
                    </blockquote>
                  ),
                  code: ({ className, children, ...props }) => {
                    const isInline = !className
                    if (isInline) {
                      return (
                        <code
                          className="bg-gray-100 text-primary-dark px-1.5 py-0.5 rounded text-sm font-mono"
                          {...props}
                        >
                          {children}
                        </code>
                      )
                    }
                    return (
                      <code className={`${className} font-mono text-sm`} {...props}>
                        {children}
                      </code>
                    )
                  },
                  pre: ({ children, ...props }) => (
                    <pre
                      className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto my-4 text-sm leading-relaxed"
                      {...props}
                    >
                      {children}
                    </pre>
                  ),
                  img: ({ src, alt }) => {
                    const isExternal = src && (src.startsWith('http://') || src.startsWith('https://'))
                    return (
                      <img
                        src={src}
                        alt={alt || ''}
                        loading="lazy"
                        {...(isExternal ? { referrerPolicy: 'no-referrer', crossOrigin: 'anonymous' } : {})}
                        className="max-w-full rounded-lg my-4 shadow-sm"
                      />
                    )
                  },
                  table: ({ children, ...props }) => (
                    <div className="overflow-x-auto my-4">
                      <table
                        className="w-full border-collapse border border-gray-300 text-sm"
                        {...props}
                      >
                        {children}
                      </table>
                    </div>
                  ),
                  thead: ({ children, ...props }) => (
                    <thead className="bg-gray-100" {...props}>
                      {children}
                    </thead>
                  ),
                  th: ({ children, ...props }) => (
                    <th
                      className="border border-gray-300 px-3 py-2 text-left font-semibold text-text"
                      {...props}
                    >
                      {children}
                    </th>
                  ),
                  td: ({ children, ...props }) => (
                    <td className="border border-gray-300 px-3 py-2 text-text" {...props}>
                      {children}
                    </td>
                  ),
                  hr: (props) => <hr className="my-6 border-gray-200" {...props} />,
                  strong: ({ children, ...props }) => (
                    <strong className="font-semibold text-text" {...props}>
                      {children}
                    </strong>
                  ),
                  a: ({ href, children, ...props }) => (
                    <a
                      href={href}
                      className="text-primary hover:text-primary-dark underline underline-offset-2 transition-colors"
                      target="_blank"
                      rel="noopener noreferrer"
                      {...props}
                    >
                      {children}
                    </a>
                  ),
                }}
              >
                {content}
              </ReactMarkdown>
            </Card>

            {metadata && (
              <Card className="mt-6">
                <h3 className="text-sm font-semibold text-text mb-3">视频信息</h3>
                <div className="flex flex-wrap gap-4 text-sm text-text-secondary">
                  {metadata.uploader && (
                    <div className="flex items-center gap-1.5">
                      <User size={14} />
                      <span>{metadata.uploader}</span>
                    </div>
                  )}
                  {metadata.duration > 0 && (
                    <div className="flex items-center gap-1.5">
                      <Clock size={14} />
                      <span>{formatDuration(metadata.duration)}</span>
                    </div>
                  )}
                  {metadata.upload_date && (
                    <div className="flex items-center gap-1.5">
                      <Calendar size={14} />
                      <span>{metadata.upload_date}</span>
                    </div>
                  )}
                  {task?.mode && (
                    <Badge variant={task.mode === 'with_images' ? 'success' : 'default'}>
                      {task.mode === 'with_images' ? '图文笔记' : '基础笔记'}
                    </Badge>
                  )}
                </div>
                {metadata.description && (
                  <p className="mt-3 text-sm text-text-secondary leading-relaxed line-clamp-3">
                    {metadata.description}
                  </p>
                )}
              </Card>
            )}
          </div>

          {toc.length > 0 && (
            <>
              <aside className="hidden lg:block w-56 flex-shrink-0">
                <div className="sticky top-20">
                  <h3 className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-3">
                    目录
                  </h3>
                  <nav className="space-y-0.5">
                    {toc.map((item) => (
                      <button
                        key={item.id}
                        onClick={() => scrollToHeading(item.id)}
                        className={`block w-full text-left text-sm py-1.5 px-2.5 rounded-md transition-colors truncate ${
                          activeTocId === item.id
                            ? 'bg-primary/10 text-primary font-medium'
                            : 'text-text-secondary hover:text-text hover:bg-gray-100'
                        } ${item.level === 2 ? 'pl-5' : ''} ${item.level === 3 ? 'pl-8' : ''}`}
                      >
                        {item.text}
                      </button>
                    ))}
                  </nav>
                </div>
              </aside>

              {tocOpen && (
                <div className="lg:hidden fixed right-4 top-16 z-40 w-64 max-h-[70vh] bg-white rounded-xl shadow-xl border border-gray-200 overflow-hidden">
                  <div className="p-3 border-b border-gray-100 flex items-center justify-between">
                    <h3 className="text-xs font-semibold text-text-secondary uppercase tracking-wider">
                      目录
                    </h3>
                    <button
                      onClick={() => setTocOpen(false)}
                      className="p-1 rounded hover:bg-gray-100 text-text-secondary"
                    >
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <line x1="18" y1="6" x2="6" y2="18" />
                        <line x1="6" y1="6" x2="18" y2="18" />
                      </svg>
                    </button>
                  </div>
                  <nav className="overflow-y-auto max-h-[calc(70vh-48px)] p-2 space-y-0.5">
                    {toc.map((item) => (
                      <button
                        key={item.id}
                        onClick={() => scrollToHeading(item.id)}
                        className={`block w-full text-left text-sm py-1.5 px-2.5 rounded-md transition-colors truncate ${
                          activeTocId === item.id
                            ? 'bg-primary/10 text-primary font-medium'
                            : 'text-text-secondary hover:text-text hover:bg-gray-100'
                        } ${item.level === 2 ? 'pl-5' : ''} ${item.level === 3 ? 'pl-8' : ''}`}
                      >
                        {item.text}
                      </button>
                    ))}
                  </nav>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}

function extractTextContent(children: React.ReactNode): string {
  if (typeof children === 'string') return children
  if (Array.isArray(children)) {
    return children
      .map((child) => {
        if (typeof child === 'string') return child
        if (child && typeof child === 'object' && 'props' in child) {
          return extractTextContent((child as { props: { children?: React.ReactNode } }).props.children)
        }
        return ''
      })
      .join('')
  }
  if (children && typeof children === 'object' && 'props' in children) {
    return extractTextContent((children as { props: { children?: React.ReactNode } }).props.children)
  }
  return ''
}
