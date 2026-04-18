import { useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  MessageSquare, FileText, BarChart3, Share2,
  GitBranch, Plus, Trash2, Clock,
  type LucideIcon,
} from 'lucide-react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { listSessions, deleteSession } from '@/api/client'
import { useStore } from '@/store/useStore'
import { formatDistanceToNow } from 'date-fns'
import type { View } from '@/types'
import { clsx } from 'clsx'

const NAV_ITEMS: { view: View; icon: LucideIcon; label: string }[] = [
  { view: 'chat',      icon: MessageSquare, label: 'Chat' },
  { view: 'documents', icon: FileText,       label: 'Documents' },
  { view: 'analytics', icon: BarChart3,      label: 'Analytics' },
  { view: 'graph',     icon: Share2,         label: 'Knowledge Graph' },
  { view: 'pipeline',  icon: GitBranch,      label: 'Pipeline' },
]

export default function Sidebar() {
  const {
    activeView, setActiveView,
    sessionId, setSessionId,
    setSessions, clearMessages
  } = useStore()

  const qc = useQueryClient()

  const { data } = useQuery({
    queryKey: ['sessions'],
    queryFn: listSessions,
    refetchInterval: 30_000,
  })

  useEffect(() => {
    if (data?.sessions) setSessions(data.sessions)
  }, [data, setSessions])

  const newSession = () => {
    const id = crypto.randomUUID()
    setSessionId(id)
    setActiveView('chat')
    qc.invalidateQueries({ queryKey: ['sessions'] })
  }

  const handleDelete = async (e: React.MouseEvent, sid: string) => {
    e.stopPropagation()
    try {
      await deleteSession(sid)
      clearMessages(sid)
      if (sid === sessionId) newSession()
      qc.invalidateQueries({ queryKey: ['sessions'] })
    } catch { /* ignore */ }
  }

  const sessions = data?.sessions ?? []

  return (
    <div className="w-72 h-full flex flex-col glass border-r border-white/5">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-white/5">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-cyan-500 to-purple-600 flex items-center justify-center glow-cyan">
            <span className="text-white font-bold text-sm">AI</span>
          </div>
          <div>
            <p className="text-sm font-semibold text-white">Enterprise Analyst</p>
            <p className="text-xs text-slate-500">v2.0 · AI-Powered</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="px-3 py-3 space-y-1 border-b border-white/5">
        {NAV_ITEMS.map(({ view, icon: Icon, label }) => (
          <button
            key={view}
            onClick={() => setActiveView(view)}
            className={clsx(
              'w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-all duration-200',
              activeView === view
                ? 'bg-gradient-to-r from-cyan-500/15 to-purple-500/15 border border-cyan-500/25 text-cyan-300'
                : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
            )}
          >
            <Icon size={16} className={activeView === view ? 'text-cyan-400' : ''} />
            {label}
            {activeView === view && (
              <motion.div
                layoutId="active-nav"
                className="ml-auto w-1.5 h-1.5 rounded-full bg-cyan-400"
              />
            )}
          </button>
        ))}
      </nav>

      {/* Sessions */}
      <div className="flex-1 flex flex-col min-h-0 px-3 py-3">
        <div className="flex items-center justify-between mb-3 px-1">
          <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">
            Conversations
          </span>
          <button
            onClick={newSession}
            className="p-1 rounded-lg hover:bg-white/10 text-slate-500 hover:text-cyan-400 transition-colors"
            title="New conversation"
          >
            <Plus size={14} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto space-y-1 pr-1">
          {sessions.length === 0 ? (
            <p className="text-xs text-slate-600 px-2 py-4 text-center">
              No conversations yet
            </p>
          ) : (
            sessions.map((s) => (
              <motion.button
                key={s.session_id}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                onClick={() => { setSessionId(s.session_id); setActiveView('chat') }}
                className={clsx(
                  'w-full group flex flex-col px-3 py-2.5 rounded-lg text-left transition-all duration-150',
                  s.session_id === sessionId
                    ? 'bg-white/8 border border-white/10'
                    : 'hover:bg-white/5'
                )}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-300 truncate flex-1 font-medium">
                    {s.title || 'Untitled'}
                  </span>
                  <button
                    onClick={(e) => handleDelete(e, s.session_id)}
                    className="opacity-0 group-hover:opacity-100 p-0.5 rounded hover:text-red-400 text-slate-600 transition-all"
                  >
                    <Trash2 size={11} />
                  </button>
                </div>
                <div className="flex items-center gap-2 mt-1">
                  <Clock size={10} className="text-slate-600" />
                  <span className="text-xs text-slate-600">
                    {s.last_activity
                      ? formatDistanceToNow(new Date(s.last_activity), { addSuffix: true })
                      : 'just now'}
                  </span>
                  <span className="ml-auto text-xs text-slate-700">
                    {s.message_count} msg{s.message_count !== 1 ? 's' : ''}
                  </span>
                </div>
              </motion.button>
            ))
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-white/5">
        <p className="text-xs text-slate-700 text-center">
          ⌘K for command palette
        </p>
      </div>
    </div>
  )
}
