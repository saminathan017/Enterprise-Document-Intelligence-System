import { useEffect, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, StopCircle, Sparkles } from 'lucide-react'
import { useStore } from '@/store/useStore'
import { useStreaming } from '@/hooks/useStreaming'
import MessageBubble from './MessageBubble'
import PipelineProgress from './PipelineProgress'
import VoiceInput from './VoiceInput'
import ExportButton from './ExportButton'

const SUGGESTED = [
  'Summarize the key findings from my documents',
  'What are the main risks identified?',
  'Generate a comparison table of the metrics',
  'What are the top recommendations?',
]

export default function ChatView() {
  const [input, setInput] = useState('')
  const { sessionId, getMessages } = useStore()
  const { isStreaming, pipelineSteps, sendMessage, abort } = useStreaming()
  const bottomRef  = useRef<HTMLDivElement>(null)
  const inputRef   = useRef<HTMLTextAreaElement>(null)
  const messages   = getMessages(sessionId)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages.length, messages[messages.length - 1]?.content])

  const handleSubmit = async () => {
    const q = input.trim()
    if (!q || isStreaming) return
    setInput('')
    await sendMessage(q)
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSubmit() }
  }

  // Auto-resize textarea
  useEffect(() => {
    const ta = inputRef.current
    if (!ta) return
    ta.style.height = 'auto'
    ta.style.height = `${Math.min(ta.scrollHeight, 160)}px`
  }, [input])

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar row */}
      {messages.length > 0 && (
        <div className="flex justify-end px-4 py-1.5 border-b border-white/5 flex-shrink-0">
          <ExportButton />
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
        {messages.length === 0 ? (
          <EmptyState onSuggest={(s) => { setInput(s); inputRef.current?.focus() }} />
        ) : (
          messages.map((msg) => <MessageBubble key={msg.id} message={msg} />)
        )}

        <AnimatePresence>
          {isStreaming && pipelineSteps.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              className="flex justify-start"
            >
              <PipelineProgress steps={pipelineSteps} />
            </motion.div>
          )}
        </AnimatePresence>
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="px-4 pb-4 flex-shrink-0">
        <div className="glass rounded-2xl border border-white/10 focus-within:border-cyan-500/40 transition-all duration-200 shadow-glass">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask anything about your documents… (Shift+Enter for newline)"
            rows={1}
            disabled={isStreaming}
            className="w-full bg-transparent px-5 pt-4 pb-2 text-sm text-slate-200 placeholder-slate-600 resize-none outline-none leading-relaxed"
          />
          <div className="flex items-center justify-between px-4 pb-3 pt-1">
            <div className="flex items-center gap-2 text-xs text-slate-600">
              <Sparkles size={12} className="text-purple-500" />
              <span>Hybrid RAG · CoT · Streaming</span>
            </div>
            <div className="flex items-center gap-2">
              {/* Voice input */}
              <VoiceInput
                onTranscript={(t) => { setInput(t); inputRef.current?.focus() }}
                disabled={isStreaming}
              />

              {isStreaming ? (
                <button
                  onClick={abort}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-red-500/20 border border-red-500/30 text-red-400 text-xs hover:bg-red-500/30 transition-colors"
                >
                  <StopCircle size={13} />
                  Stop
                </button>
              ) : (
                <button
                  onClick={handleSubmit}
                  disabled={!input.trim()}
                  className="flex items-center gap-1.5 px-4 py-1.5 rounded-xl bg-gradient-to-r from-cyan-500/20 to-purple-500/20 border border-cyan-500/30 text-cyan-300 text-xs font-medium hover:from-cyan-500/30 hover:to-purple-500/30 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
                >
                  <Send size={13} />
                  Send
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function EmptyState({ onSuggest }: { onSuggest: (s: string) => void }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col items-center justify-center h-full min-h-[400px] text-center px-8"
    >
      <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-cyan-500/20 to-purple-500/20 border border-cyan-500/20 flex items-center justify-center mb-6 glow-cyan">
        <Sparkles size={28} className="text-cyan-400" />
      </div>
      <h2 className="text-xl font-semibold text-white mb-2">Start with a question</h2>
      <p className="text-slate-500 text-sm mb-8 max-w-md">
        Upload documents and ask anything. Answers are grounded in your data with source citations, chain-of-thought reasoning, and NLI faithfulness scoring.
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-lg">
        {SUGGESTED.map((s) => (
          <button
            key={s}
            onClick={() => onSuggest(s)}
            className="glass border border-white/8 rounded-xl px-4 py-3 text-sm text-slate-400 hover:text-cyan-300 hover:border-cyan-500/30 text-left transition-all duration-200"
          >
            {s}
          </button>
        ))}
      </div>
    </motion.div>
  )
}
