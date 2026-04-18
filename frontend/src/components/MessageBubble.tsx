import { useState } from 'react'
import { motion } from 'framer-motion'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { Copy, Check, BookOpen, Clock } from 'lucide-react'
import { clsx } from 'clsx'
import type { Message } from '@/types'
import { useStore } from '@/store/useStore'
import CitationCard from './CitationCard'
import FeedbackButtons from './FeedbackButtons'

interface Props { message: Message }

export default function MessageBubble({ message }: Props) {
  const [copied, setCopied]             = useState(false)
  const [showCitations, setShowCitations] = useState(false)
  const { sessionId, model } = useStore()
  const isUser = message.role === 'user'

  const copyContent = () => {
    navigator.clipboard.writeText(message.content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  // Extract last user message for feedback context
  const userQuery = message.role === 'assistant'
    ? '' // filled by parent query stored in store; feedback passes it along
    : message.content

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className={clsx('flex gap-3', isUser ? 'justify-end' : 'justify-start')}
    >
      {/* AI avatar */}
      {!isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-xl bg-gradient-to-br from-cyan-500 to-purple-600 flex items-center justify-center mt-0.5">
          <span className="text-white text-xs font-bold">AI</span>
        </div>
      )}

      <div className={clsx('flex flex-col max-w-[75%]', isUser && 'items-end')}>
        {/* Bubble */}
        <div
          className={clsx(
            'relative rounded-2xl px-4 py-3 text-sm leading-relaxed',
            isUser
              ? 'bg-gradient-to-r from-cyan-500/15 to-purple-500/15 border border-cyan-500/20 text-slate-200 rounded-tr-sm'
              : 'glass border border-white/8 text-slate-200 rounded-tl-sm'
          )}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className={clsx(message.isStreaming && !message.content && 'min-h-[24px]')}>
              {message.content ? (
                <div className={clsx('prose prose-invert prose-sm max-w-none', message.isStreaming && 'streaming-cursor')}>
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                      code({ className, children, ...props }) {
                        const match = /language-(\w+)/.exec(className ?? '')
                        const isBlock = !!(props as { inline?: boolean }).inline === false && match
                        return isBlock ? (
                          <SyntaxHighlighter
                            style={oneDark}
                            language={match![1]}
                            PreTag="div"
                            customStyle={{ borderRadius: '0.75rem', fontSize: '0.8rem', margin: '0.5rem 0', background: 'rgba(0,0,0,0.4)' }}
                          >
                            {String(children).replace(/\n$/, '')}
                          </SyntaxHighlighter>
                        ) : (
                          <code className="bg-black/30 text-cyan-300 rounded px-1 py-0.5 font-mono text-xs" {...props}>
                            {children}
                          </code>
                        )
                      },
                      table({ children }) {
                        return (
                          <div className="overflow-x-auto my-2">
                            <table className="min-w-full text-xs border-collapse">{children}</table>
                          </div>
                        )
                      },
                      th({ children }) {
                        return <th className="border border-white/10 px-3 py-1.5 bg-white/5 text-left text-cyan-300 font-medium">{children}</th>
                      },
                      td({ children }) {
                        return <td className="border border-white/10 px-3 py-1.5 text-slate-300">{children}</td>
                      },
                    }}
                  >
                    {message.content}
                  </ReactMarkdown>
                </div>
              ) : (
                <span className="streaming-cursor text-transparent">.</span>
              )}
            </div>
          )}
        </div>

        {/* Actions row — only on completed AI messages */}
        {!isUser && !message.isStreaming && message.content && (
          <div className="flex items-center gap-3 mt-2 px-1 flex-wrap">
            {/* Copy */}
            <button
              onClick={copyContent}
              className="flex items-center gap-1 text-xs text-slate-600 hover:text-slate-300 transition-colors"
            >
              {copied ? <Check size={12} className="text-emerald-400" /> : <Copy size={12} />}
              {copied ? 'Copied' : 'Copy'}
            </button>

            {/* Citations toggle */}
            {(message.citations?.length ?? 0) > 0 && (
              <button
                onClick={() => setShowCitations((v) => !v)}
                className="flex items-center gap-1 text-xs text-slate-600 hover:text-cyan-400 transition-colors"
              >
                <BookOpen size={12} />
                {message.citations!.length} source{message.citations!.length > 1 ? 's' : ''}
              </button>
            )}

            {/* Processing time */}
            {message.processingMs && (
              <span className="flex items-center gap-1 text-xs text-slate-700">
                <Clock size={11} />
                {(message.processingMs / 1000).toFixed(1)}s
              </span>
            )}

            {/* Feedback — separator then thumbs */}
            <span className="text-slate-800 text-xs">·</span>
            <FeedbackButtons
              messageId={message.id}
              sessionId={sessionId}
              query={message.content.slice(0, 200)}
              answer={message.content}
              model={model}
              processingMs={message.processingMs}
            />
          </div>
        )}

        {/* Citations panel */}
        {showCitations && (message.citations?.length ?? 0) > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            className="mt-2 space-y-2 w-full"
          >
            {message.citations!.map((c, i) => (
              <CitationCard key={i} citation={c} index={i + 1} />
            ))}
          </motion.div>
        )}
      </div>

      {/* User avatar */}
      {isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-xl bg-gradient-to-br from-slate-700 to-slate-600 border border-white/10 flex items-center justify-center mt-0.5">
          <span className="text-slate-300 text-xs font-bold">U</span>
        </div>
      )}
    </motion.div>
  )
}
