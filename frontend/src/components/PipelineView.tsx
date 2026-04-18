import { motion } from 'framer-motion'
import { GitBranch, Upload, Search, Cpu, BookOpen, ChevronRight, Zap } from 'lucide-react'
import { clsx } from 'clsx'
import { useStore } from '@/store/useStore'

const INGESTION_STEPS = [
  { icon: Upload,   label: 'Document Upload',   desc: 'PDF, TXT, Markdown via REST API', color: 'cyan' },
  { icon: BookOpen, label: 'Text Extraction',    desc: 'PyPDF2 parser + unicode normalisation', color: 'cyan' },
  { icon: Cpu,      label: 'Semantic Chunking',  desc: '1000 char chunks · 300 overlap', color: 'cyan' },
  { icon: Cpu,      label: 'Embedding',          desc: 'all-MiniLM-L6-v2 (local, no API cost)', color: 'cyan' },
  { icon: Search,   label: 'Vector Store',       desc: 'ChromaDB persistent collection', color: 'cyan' },
]

const QUERY_STEPS = [
  { icon: BookOpen, label: 'Query Received',     desc: 'Session context + history loaded', color: 'purple' },
  { icon: Cpu,      label: 'HyDE (optional)',    desc: 'Hypothetical doc → richer retrieval', color: 'purple', optional: true },
  { icon: Search,   label: 'Similarity Search',  desc: 'Top-K cosine similarity in ChromaDB', color: 'purple' },
  { icon: Cpu,      label: 'Cross-Encoder Rerank', desc: 'ms-marco MiniLM — score blending 40/60', color: 'purple', optional: true },
  { icon: Cpu,      label: 'Context Assembly',   desc: 'Sorted, cited, token-budgeted', color: 'purple' },
  { icon: Zap,      label: 'LLM Generation',     desc: 'GPT-4o streaming via SSE', color: 'purple' },
  { icon: BookOpen, label: 'Citations + Memory', desc: 'Source tracking · session persist', color: 'purple' },
]

const COLOR_MAP = {
  cyan:   { dot: 'bg-cyan-500', text: 'text-cyan-400', border: 'border-cyan-500/20', bg: 'bg-cyan-500/8' },
  purple: { dot: 'bg-red-500', text: 'text-red-400', border: 'border-red-500/20', bg: 'bg-red-500/8' },
}

function PipelineColumn({
  title, steps, badge
}: {
  title: string
  steps: typeof INGESTION_STEPS
  badge: string
}) {
  const color = steps[0].color as 'cyan' | 'purple'
  const c = COLOR_MAP[color]

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex-1 glass border border-white/8 rounded-2xl overflow-hidden"
    >
      <div className={clsx('px-5 py-4 border-b border-white/5', c.bg)}>
        <div className="flex items-center gap-3">
          <span className={clsx('text-xs px-2 py-0.5 rounded-full border font-mono font-medium', c.border, c.text)}>
            {badge}
          </span>
          <h3 className="text-sm font-semibold text-slate-200">{title}</h3>
        </div>
      </div>

      <div className="p-4 space-y-1">
        {steps.map((step, i) => {
          const Icon = step.icon
          const sc = COLOR_MAP[step.color as 'cyan' | 'purple']
          return (
            <div key={i} className="relative">
              <div className="flex gap-3 p-3 rounded-xl hover:bg-white/3 transition-colors group">
                {/* Step number + connector */}
                <div className="flex flex-col items-center">
                  <div className={clsx(
                    'w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 text-xs font-bold transition-all',
                    sc.bg, sc.text
                  )}>
                    {i + 1}
                  </div>
                  {i < steps.length - 1 && (
                    <div className={clsx('w-0.5 h-full mt-1 rounded-full opacity-20', sc.dot)} />
                  )}
                </div>

                <div className="flex-1 min-w-0 pt-1">
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-medium text-slate-200">{step.label}</p>
                    {(step as any).optional && (
                      <span className="text-xs text-slate-600 border border-white/10 rounded-full px-1.5 py-0.5">
                        optional
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-600 mt-0.5 leading-relaxed">{step.desc}</p>
                </div>

                <Icon size={14} className={clsx('mt-1.5 flex-shrink-0 opacity-40', sc.text)} />
              </div>

              {i < steps.length - 1 && (
                <div className="flex justify-start pl-7 my-0.5">
                  <ChevronRight size={10} className="text-slate-700 rotate-90" />
                </div>
              )}
            </div>
          )
        })}
      </div>
    </motion.div>
  )
}

function FeatureBadge({ label, desc }: { label: string; desc: string }) {
  return (
    <div className="glass border border-white/8 rounded-xl px-4 py-3">
      <p className="text-sm font-medium text-slate-200">{label}</p>
      <p className="text-xs text-slate-600 mt-0.5">{desc}</p>
    </div>
  )
}

export default function PipelineView() {
  const { useHyde, model } = useStore()

  return (
    <div className="h-full overflow-y-auto px-6 py-6 space-y-6">
      {/* Active config banner */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="glass border border-white/8 rounded-2xl px-5 py-4 flex flex-wrap items-center gap-4"
      >
        <div className="flex items-center gap-2">
          <GitBranch size={16} className="text-cyan-400" />
          <span className="text-sm font-semibold text-slate-200">Active Configuration</span>
        </div>
        <div className="flex flex-wrap gap-2 ml-auto">
          <span className="px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-300 text-xs font-mono">
            {model}
          </span>
          <span className={clsx(
            'px-3 py-1 rounded-full border text-xs font-mono',
            useHyde
              ? 'bg-red-500/10 border-red-500/20 text-red-300'
              : 'bg-white/5 border-white/10 text-slate-500'
          )}>
            HyDE: {useHyde ? 'ON' : 'OFF'}
          </span>
          <span className="px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs font-mono">
            SSE Streaming
          </span>
        </div>
      </motion.div>

      {/* Pipeline columns */}
      <div className="flex gap-5 min-h-0">
        <PipelineColumn title="Document Ingestion"  steps={INGESTION_STEPS} badge="INGEST" />
        <PipelineColumn title="Query & Generation"  steps={QUERY_STEPS}     badge="QUERY"  />
      </div>

      {/* Technology grid */}
      <div>
        <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
          Technology Stack
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <FeatureBadge label="FastAPI + SSE"        desc="Async · token streaming" />
          <FeatureBadge label="ChromaDB"             desc="Persistent vector store" />
          <FeatureBadge label="Sentence Transformers" desc="Local MiniLM embeddings" />
          <FeatureBadge label="LangChain"            desc="RAG orchestration" />
          <FeatureBadge label="OpenAI GPT-4o"        desc="Generation + entity NER" />
          <FeatureBadge label="React 18 + Vite"      desc="SSE client · Zustand" />
          <FeatureBadge label="Three.js"             desc="3D neural background" />
          <FeatureBadge label="Cytoscape.js"         desc="Knowledge graph viz" />
        </div>
      </div>
    </div>
  )
}
