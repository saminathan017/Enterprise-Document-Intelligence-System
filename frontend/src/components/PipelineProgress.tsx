import { motion } from 'framer-motion'
import { Search, FileText, Cpu, CheckCircle, Loader, type LucideIcon } from 'lucide-react'
import { clsx } from 'clsx'
import type { PipelineStep } from '@/types'

const STEP_META: Record<string, { icon: LucideIcon; label: string }> = {
  retrieval:  { icon: Search,   label: 'Retrieving' },
  hyde:       { icon: Cpu,      label: 'HyDE' },
  context:    { icon: FileText, label: 'Context' },
  generation: { icon: Cpu,      label: 'Generating' },
}

interface Props {
  steps: PipelineStep[]
}

export default function PipelineProgress({ steps }: Props) {
  return (
    <div className="glass border border-white/8 rounded-xl px-4 py-3 max-w-sm">
      <p className="text-xs text-slate-600 mb-2 font-medium">RAG Pipeline</p>
      <div className="space-y-1.5">
        {steps.map((step, i) => {
          const meta = STEP_META[step.step] ?? { icon: Cpu, label: step.step }
          const Icon = meta.icon
          return (
            <motion.div
              key={step.step}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.05 }}
              className="flex items-center gap-2.5"
            >
              {step.status === 'done' ? (
                <CheckCircle size={13} className="text-emerald-400 flex-shrink-0" />
              ) : step.status === 'running' ? (
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                >
                  <Loader size={13} className="text-cyan-400 flex-shrink-0" />
                </motion.div>
              ) : (
                <div className="w-3 h-3 rounded-full border border-white/20 flex-shrink-0" />
              )}
              <span className={clsx(
                'text-xs',
                step.status === 'done' ? 'text-slate-400' :
                step.status === 'running' ? 'text-cyan-300' : 'text-slate-600'
              )}>
                {step.message ?? meta.label}
                {step.count != null && step.status === 'done' && (
                  <span className="text-slate-600 ml-1">· {step.count} docs</span>
                )}
                {step.elapsed_ms != null && step.status === 'done' && (
                  <span className="text-slate-700 ml-1">({step.elapsed_ms}ms)</span>
                )}
              </span>
            </motion.div>
          )
        })}
      </div>
    </div>
  )
}
