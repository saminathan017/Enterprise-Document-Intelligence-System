import { motion } from 'framer-motion'
import { FileText, TrendingUp } from 'lucide-react'
import type { Citation } from '@/types'
import { clsx } from 'clsx'

interface Props {
  citation: Citation
  index: number
}

export default function CitationCard({ citation, index }: Props) {
  const scoreColor =
    citation.score >= 0.8
      ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20'
      : citation.score >= 0.6
      ? 'text-cyan-400 bg-cyan-500/10 border-cyan-500/20'
      : 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20'

  const scoreBar = Math.round(citation.score * 100)

  return (
    <motion.div
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.05 }}
      className="glass border border-white/8 rounded-xl p-3 text-xs"
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex items-center gap-2 min-w-0">
          <div className="w-5 h-5 rounded-lg bg-gradient-to-br from-cyan-500/20 to-purple-500/20 border border-white/10 flex items-center justify-center flex-shrink-0">
            <span className="text-cyan-400 font-mono text-[10px]">{index}</span>
          </div>
          <div className="flex items-center gap-1.5 min-w-0">
            <FileText size={11} className="text-slate-500 flex-shrink-0" />
            <span className="text-slate-300 font-medium truncate">{citation.source}</span>
          </div>
        </div>

        <div className={clsx('flex items-center gap-1 px-2 py-0.5 rounded-full border text-[10px] font-medium flex-shrink-0', scoreColor)}>
          <TrendingUp size={9} />
          {scoreBar}%
        </div>
      </div>

      {/* Score bar */}
      <div className="h-0.5 bg-white/5 rounded-full mb-2 overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${scoreBar}%` }}
          transition={{ duration: 0.6, delay: index * 0.05 }}
          className={clsx(
            'h-full rounded-full',
            citation.score >= 0.8 ? 'bg-emerald-400' :
            citation.score >= 0.6 ? 'bg-cyan-400' : 'bg-yellow-400'
          )}
        />
      </div>

      {/* Excerpt */}
      <p className="text-slate-500 leading-relaxed line-clamp-3">{citation.excerpt}</p>

      {citation.chunk_id && (
        <p className="mt-1.5 text-slate-700 font-mono text-[10px]">{citation.chunk_id}</p>
      )}
    </motion.div>
  )
}
