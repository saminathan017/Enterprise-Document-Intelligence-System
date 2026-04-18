import { useState, useCallback, useRef } from 'react'
import { streamQuery } from '@/api/client'
import { useStore } from '@/store/useStore'
import type { PipelineStep, Citation } from '@/types'

interface UseStreamingReturn {
  isStreaming: boolean
  pipelineSteps: PipelineStep[]
  sendMessage: (query: string) => Promise<void>
  abort: () => void
}

export function useStreaming(): UseStreamingReturn {
  const [isStreaming, setIsStreaming] = useState(false)
  const [pipelineSteps, setPipelineSteps] = useState<PipelineStep[]>([])
  const abortRef = useRef(false)

  const { sessionId, model, useHyde, topK, addMessage, updateMessage } = useStore()

  const sendMessage = useCallback(
    async (query: string) => {
      if (isStreaming) return

      abortRef.current = false
      setIsStreaming(true)
      setPipelineSteps([])

      // Add user message immediately
      const userMsgId = crypto.randomUUID()
      addMessage(sessionId, {
        id: userMsgId,
        role: 'user',
        content: query,
        createdAt: Date.now(),
      })

      // Add placeholder assistant message
      const assistantMsgId = crypto.randomUUID()
      addMessage(sessionId, {
        id: assistantMsgId,
        role: 'assistant',
        content: '',
        isStreaming: true,
        createdAt: Date.now(),
        pipelineSteps: [],
      })

      let accumulated = ''
      let finalCitations: Citation[] = []

      try {
        const gen = streamQuery({
          query,
          session_id: sessionId,
          top_k: topK,
          model,
          use_hyde: useHyde,
          use_crag: true,
          expand_parents: true,
          use_compression: false,
        })

        for await (const event of gen) {
          if (abortRef.current) break

          if (event.type === 'step') {
            const step = {
              step: event.step,
              status: event.status,
              message: event.message,
              elapsed_ms: event.elapsed_ms,
              count: event.count,
              tokens: event.tokens,
            }
            setPipelineSteps((prev) => {
              const idx = prev.findIndex((s) => s.step === event.step)
              if (idx >= 0) {
                const next = [...prev]
                next[idx] = step
                return next
              }
              return [...prev, step]
            })
            updateMessage(sessionId, assistantMsgId, {
              pipelineSteps: [...pipelineSteps],
            })
          } else if (event.type === 'token') {
            accumulated += event.content
            updateMessage(sessionId, assistantMsgId, {
              content: accumulated,
              isStreaming: true,
            })
          } else if (event.type === 'citations') {
            finalCitations = event.citations
          } else if (event.type === 'done') {
            updateMessage(sessionId, assistantMsgId, {
              content: accumulated,
              citations: finalCitations,
              isStreaming: false,
              processingMs: event.elapsed_ms,
            })
          } else if (event.type === 'error') {
            updateMessage(sessionId, assistantMsgId, {
              content: `⚠ Error: ${event.message}`,
              isStreaming: false,
            })
          }
        }
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err)
        updateMessage(sessionId, assistantMsgId, {
          content: `⚠ Connection error: ${msg}`,
          isStreaming: false,
        })
      } finally {
        updateMessage(sessionId, assistantMsgId, { isStreaming: false })
        setIsStreaming(false)
        setPipelineSteps([])
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [isStreaming, sessionId, model, useHyde, topK]
  )

  const abort = useCallback(() => {
    abortRef.current = true
    setIsStreaming(false)
  }, [])

  return { isStreaming, pipelineSteps, sendMessage, abort }
}
