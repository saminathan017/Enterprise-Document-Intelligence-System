import { useState } from 'react'
import { ThumbsUp, ThumbsDown, Check } from 'lucide-react'
import { motion } from 'framer-motion'
import { clsx } from 'clsx'
import { submitFeedback } from '@/api/client'

interface Props {
  messageId: string
  sessionId: string
  query: string
  answer: string
  model?: string
  processingMs?: number
}

export default function FeedbackButtons({ messageId, sessionId, query, answer, model, processingMs }: Props) {
  const [voted, setVoted]   = useState<'up' | 'down' | null>(null)
  const [loading, setLoading] = useState(false)

  const submit = async (rating: 1 | -1) => {
    if (voted || loading) return
    setLoading(true)
    try {
      await submitFeedback({
        session_id:    sessionId,
        message_id:    messageId,
        query,
        answer,
        rating,
        model,
        processing_ms: processingMs,
      })
      setVoted(rating === 1 ? 'up' : 'down')
    } catch {
      /* silent — don't interrupt UX */
    } finally {
      setLoading(false)
    }
  }

  if (voted) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        className="flex items-center gap-1 text-xs text-slate-600"
      >
        <Check size={11} className={voted === 'up' ? 'text-emerald-400' : 'text-red-400'} />
        <span>Feedback recorded</span>
      </motion.div>
    )
  }

  return (
    <div className="flex items-center gap-1">
      {([['up', 1, ThumbsUp, 'hover:text-emerald-400'], ['down', -1, ThumbsDown, 'hover:text-red-400']] as const).map(
        ([dir, rating, Icon, hoverCls]) => (
          <motion.button
            key={dir}
            whileTap={{ scale: 0.85 }}
            onClick={() => submit(rating as 1 | -1)}
            disabled={loading}
            title={dir === 'up' ? 'Good answer' : 'Poor answer'}
            className={clsx(
              'p-1 rounded-lg transition-colors duration-150 text-slate-700 disabled:opacity-40',
              hoverCls
            )}
          >
            <Icon size={12} />
          </motion.button>
        )
      )}
    </div>
  )
}
