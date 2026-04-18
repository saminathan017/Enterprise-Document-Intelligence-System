import { useState, useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import { Search, MessageSquare, FileText, BarChart3, Share2, GitBranch, Plus, X, type LucideIcon } from 'lucide-react'
import { useStore } from '@/store/useStore'
import { clsx } from 'clsx'
import type { View } from '@/types'

interface Command {
  id: string
  label: string
  description: string
  icon: LucideIcon
  action: () => void
  category: string
}

export default function CommandPalette() {
  const [query, setQuery] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)
  const { setCommandPaletteOpen, setActiveView, setSessionId } = useStore()

  const close = () => setCommandPaletteOpen(false)

  const allCommands: Command[] = [
    {
      id: 'chat',
      label: 'Open Chat',
      description: 'Go to AI chat interface',
      icon: MessageSquare,
      action: () => { setActiveView('chat'); close() },
      category: 'Navigation',
    },
    {
      id: 'documents',
      label: 'Document Library',
      description: 'Manage and upload documents',
      icon: FileText,
      action: () => { setActiveView('documents'); close() },
      category: 'Navigation',
    },
    {
      id: 'analytics',
      label: 'Analytics Dashboard',
      description: 'View usage metrics and charts',
      icon: BarChart3,
      action: () => { setActiveView('analytics'); close() },
      category: 'Navigation',
    },
    {
      id: 'graph',
      label: 'Knowledge Graph',
      description: 'Visualize entity relationships',
      icon: Share2,
      action: () => { setActiveView('graph'); close() },
      category: 'Navigation',
    },
    {
      id: 'pipeline',
      label: 'RAG Pipeline',
      description: 'Explore the AI architecture',
      icon: GitBranch,
      action: () => { setActiveView('pipeline'); close() },
      category: 'Navigation',
    },
    {
      id: 'new-session',
      label: 'New Conversation',
      description: 'Start a fresh chat session',
      icon: Plus,
      action: () => {
        setSessionId(crypto.randomUUID())
        setActiveView('chat')
        close()
      },
      category: 'Actions',
    },
  ]

  const filtered = query
    ? allCommands.filter(
        (c) =>
          c.label.toLowerCase().includes(query.toLowerCase()) ||
          c.description.toLowerCase().includes(query.toLowerCase())
      )
    : allCommands

  const grouped: Record<string, Command[]> = {}
  for (const cmd of filtered) {
    if (!grouped[cmd.category]) grouped[cmd.category] = []
    grouped[cmd.category].push(cmd)
  }

  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  const [selectedIdx, setSelectedIdx] = useState(0)

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setSelectedIdx((i) => Math.min(i + 1, filtered.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setSelectedIdx((i) => Math.max(i - 1, 0))
    } else if (e.key === 'Enter') {
      filtered[selectedIdx]?.action()
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh] px-4"
      onClick={close}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />

      {/* Palette */}
      <motion.div
        initial={{ scale: 0.96, y: -16 }}
        animate={{ scale: 1, y: 0 }}
        exit={{ scale: 0.96, y: -16 }}
        transition={{ type: 'spring', stiffness: 400, damping: 30 }}
        onClick={(e) => e.stopPropagation()}
        className="relative w-full max-w-lg glass border border-white/15 rounded-2xl shadow-[0_32px_80px_rgba(0,0,0,0.6)] overflow-hidden"
      >
        {/* Search input */}
        <div className="flex items-center gap-3 px-4 py-3.5 border-b border-white/8">
          <Search size={16} className="text-slate-500 flex-shrink-0" />
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => { setQuery(e.target.value); setSelectedIdx(0) }}
            onKeyDown={handleKeyDown}
            placeholder="Search commands…"
            className="flex-1 bg-transparent text-sm text-slate-200 placeholder-slate-600 outline-none"
          />
          <button onClick={close} className="p-1 rounded-lg hover:bg-white/10 text-slate-600 hover:text-slate-300 transition-colors">
            <X size={14} />
          </button>
        </div>

        {/* Results */}
        <div className="max-h-80 overflow-y-auto py-1.5">
          {filtered.length === 0 ? (
            <p className="text-sm text-slate-600 text-center py-8">No commands found</p>
          ) : (
            Object.entries(grouped).map(([category, cmds]) => (
              <div key={category}>
                <p className="px-4 py-1.5 text-[10px] font-semibold text-slate-600 uppercase tracking-wider">
                  {category}
                </p>
                {cmds.map((cmd, i) => {
                  const globalIdx = filtered.indexOf(cmd)
                  const Icon = cmd.icon
                  return (
                    <button
                      key={cmd.id}
                      onClick={cmd.action}
                      onMouseEnter={() => setSelectedIdx(globalIdx)}
                      className={clsx(
                        'w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors',
                        selectedIdx === globalIdx ? 'bg-cyan-500/10' : 'hover:bg-white/5'
                      )}
                    >
                      <div className={clsx(
                        'w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 transition-colors',
                        selectedIdx === globalIdx ? 'bg-cyan-500/20' : 'bg-white/5'
                      )}>
                        <Icon size={15} className={selectedIdx === globalIdx ? 'text-cyan-400' : 'text-slate-400'} />
                      </div>
                      <div>
                        <p className={clsx('text-sm font-medium', selectedIdx === globalIdx ? 'text-cyan-300' : 'text-slate-200')}>
                          {cmd.label}
                        </p>
                        <p className="text-xs text-slate-600">{cmd.description}</p>
                      </div>
                    </button>
                  )
                })}
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-2 border-t border-white/5 flex items-center gap-4 text-[10px] text-slate-700">
          <span>↑↓ navigate</span>
          <span>↵ select</span>
          <span>ESC close</span>
        </div>
      </motion.div>
    </motion.div>
  )
}
