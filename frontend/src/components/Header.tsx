import { useQuery } from '@tanstack/react-query'
import { PanelLeft, Zap, Settings, ChevronDown, Cpu } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { useState } from 'react'
import { useStore } from '@/store/useStore'
import { healthCheck } from '@/api/client'
import type { Model } from '@/types'
import { clsx } from 'clsx'

const MODELS: { id: Model; label: string; desc: string }[] = [
  { id: 'gpt-4o',           label: 'GPT-4o',           desc: 'Most capable · Slower' },
  { id: 'gpt-4o-mini',      label: 'GPT-4o Mini',      desc: 'Fast · Cost-efficient' },
  { id: 'gpt-4-turbo-preview', label: 'GPT-4 Turbo',  desc: 'Balanced · 128k ctx' },
]

export default function Header() {
  const { toggleSidebar, model, setModel, useHyde, setUseHyde, activeView } = useStore()
  const [modelMenuOpen, setModelMenuOpen] = useState(false)

  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: healthCheck,
    refetchInterval: 60_000,
  })

  const currentModel = MODELS.find((m) => m.id === model) ?? MODELS[0]

  const viewLabels: Record<string, string> = {
    chat: 'AI Chat',
    documents: 'Document Library',
    analytics: 'Analytics Dashboard',
    graph: 'Knowledge Graph',
    pipeline: 'RAG Pipeline',
  }

  return (
    <header className="flex items-center justify-between px-5 py-3 glass border-b border-white/5 flex-shrink-0">
      {/* Left */}
      <div className="flex items-center gap-4">
        <button
          onClick={toggleSidebar}
          className="p-1.5 rounded-lg hover:bg-white/10 text-slate-400 hover:text-slate-200 transition-colors"
        >
          <PanelLeft size={18} />
        </button>
        <h1 className="text-sm font-semibold text-slate-200">
          {viewLabels[activeView] ?? 'Enterprise Document Intelligence'}
        </h1>
      </div>

      {/* Center — model selector */}
      <div className="relative">
        <button
          onClick={() => setModelMenuOpen((v) => !v)}
          className="flex items-center gap-2 px-3 py-1.5 rounded-xl glass border border-white/10 hover:border-cyan-500/30 transition-all text-sm"
        >
          <Cpu size={14} className="text-cyan-400" />
          <span className="text-slate-200">{currentModel.label}</span>
          <ChevronDown size={12} className={clsx('text-slate-500 transition-transform', modelMenuOpen && 'rotate-180')} />
        </button>

        <AnimatePresence>
          {modelMenuOpen && (
            <motion.div
              initial={{ opacity: 0, y: -8, scale: 0.96 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -8, scale: 0.96 }}
              transition={{ duration: 0.15 }}
              className="absolute top-full mt-2 left-1/2 -translate-x-1/2 w-56 glass rounded-xl border border-white/10 shadow-glass z-50 py-1"
            >
              {MODELS.map((m) => (
                <button
                  key={m.id}
                  onClick={() => { setModel(m.id); setModelMenuOpen(false) }}
                  className={clsx(
                    'w-full flex flex-col px-4 py-2.5 text-left transition-colors text-sm hover:bg-white/5',
                    m.id === model && 'bg-cyan-500/10'
                  )}
                >
                  <span className={clsx('font-medium', m.id === model ? 'text-cyan-300' : 'text-slate-200')}>
                    {m.label}
                  </span>
                  <span className="text-xs text-slate-500 mt-0.5">{m.desc}</span>
                </button>
              ))}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Right */}
      <div className="flex items-center gap-3">
        {/* HyDE toggle */}
        <button
          onClick={() => setUseHyde(!useHyde)}
          title="HyDE: Hypothetical Document Embeddings"
          className={clsx(
            'flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium transition-all border',
            useHyde
              ? 'bg-red-500/20 border-red-500/40 text-red-300'
              : 'border-white/10 text-slate-500 hover:text-slate-300 hover:border-white/20'
          )}
        >
          <Zap size={12} />
          HyDE
        </button>

        {/* Health indicator */}
        <div className="flex items-center gap-2">
          <div
            className={clsx(
              'w-2 h-2 rounded-full',
              health?.status === 'healthy' ? 'bg-emerald-400 glow-cyan' : 'bg-red-400'
            )}
          />
          <span className="text-xs text-slate-500">
            {health ? `${health.indexed_chunks ?? 0} chunks` : 'connecting…'}
          </span>
        </div>

        <button className="p-1.5 rounded-lg hover:bg-white/10 text-slate-400 hover:text-slate-200 transition-colors">
          <Settings size={16} />
        </button>
      </div>
    </header>
  )
}
