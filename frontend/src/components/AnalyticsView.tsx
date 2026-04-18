import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts'
import {
  MessageSquare, FileText, Users, Activity,
  ThumbsUp, ThumbsDown, DollarSign, Cpu,
  type LucideIcon,
} from 'lucide-react'
import { getAnalytics, getFeedbackSummary, getCosts } from '@/api/client'
import { formatDistanceToNow } from 'date-fns'

const CHART_COLORS = { primary: '#00d4ff', secondary: '#8b5cf6', grid: 'rgba(255,255,255,0.05)' }

function StatCard({
  icon: Icon, label, value, sub, color
}: {
  icon: LucideIcon
  label: string
  value: number | string
  sub?: string
  color: 'cyan' | 'purple' | 'emerald' | 'yellow' | 'rose' | 'orange'
}) {
  const colors = {
    cyan:    { bg: 'bg-cyan-500/10',    text: 'text-cyan-400',    glow: 'shadow-[0_0_20px_rgba(0,212,255,0.15)]' },
    purple:  { bg: 'bg-purple-500/10',  text: 'text-purple-400',  glow: 'shadow-[0_0_20px_rgba(139,92,246,0.15)]' },
    emerald: { bg: 'bg-emerald-500/10', text: 'text-emerald-400', glow: '' },
    yellow:  { bg: 'bg-yellow-500/10',  text: 'text-yellow-400',  glow: '' },
    rose:    { bg: 'bg-rose-500/10',    text: 'text-rose-400',    glow: '' },
    orange:  { bg: 'bg-orange-500/10',  text: 'text-orange-400',  glow: '' },
  }
  const c = colors[color]
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className={`glass border border-white/8 rounded-2xl p-5 ${c.glow}`}
    >
      <div className="flex items-start justify-between mb-4">
        <div className={`w-10 h-10 rounded-xl ${c.bg} flex items-center justify-center`}>
          <Icon size={18} className={c.text} />
        </div>
      </div>
      <p className="text-3xl font-bold text-white mb-1">{value}</p>
      <p className="text-sm font-medium text-slate-300">{label}</p>
      {sub && <p className="text-xs text-slate-600 mt-0.5">{sub}</p>}
    </motion.div>
  )
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null
  return (
    <div className="glass border border-white/10 rounded-xl px-4 py-2 text-xs shadow-glass">
      <p className="text-slate-400 mb-1">{label}</p>
      {payload.map((p: any, i: number) => (
        <p key={i} style={{ color: p.color }}>{p.name}: <strong>{p.value}</strong></p>
      ))}
    </div>
  )
}

export default function AnalyticsView() {
  const { data, isLoading } = useQuery({
    queryKey: ['analytics'],
    queryFn: getAnalytics,
    refetchInterval: 15_000,
  })
  const { data: feedback } = useQuery({
    queryKey: ['feedback-summary'],
    queryFn: getFeedbackSummary,
    refetchInterval: 30_000,
  })
  const { data: costs } = useQuery({
    queryKey: ['costs'],
    queryFn: getCosts,
    refetchInterval: 30_000,
  })

  const activityData = (() => {
    if (!data?.sessions) return []
    const buckets: Record<string, { date: string; queries: number; sessions: number }> = {}
    data.sessions.forEach((s) => {
      const key = s.last_activity?.slice(0, 10) ?? 'unknown'
      if (!buckets[key]) buckets[key] = { date: key, queries: 0, sessions: 0 }
      buckets[key].queries += s.message_count
      buckets[key].sessions += 1
    })
    return Object.values(buckets).sort((a, b) => a.date.localeCompare(b.date)).slice(-14)
  })()

  const distData = (() => {
    if (!data?.sessions) return []
    const ranges = [
      { range: '1-5',  min: 1,  max: 5 },
      { range: '6-10', min: 6,  max: 10 },
      { range: '11-20', min: 11, max: 20 },
      { range: '21+',  min: 21, max: Infinity },
    ]
    return ranges.map(({ range, min, max }) => ({
      range,
      count: data.sessions.filter((s) => s.message_count >= min && s.message_count <= max).length,
    }))
  })()

  const modelCostData = (() => {
    if (!costs?.by_model) return []
    return Object.entries(costs.by_model).map(([model, v]) => ({
      model: model.replace('gpt-', '').replace('-preview', ''),
      tokens: v.input + v.output,
      cost: parseFloat(v.cost.toFixed(4)),
    }))
  })()

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-cyan-500/30 border-t-cyan-400 rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="h-full overflow-y-auto px-6 py-6 space-y-6">
      {/* KPI cards — row 1 */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={FileText}      label="Documents"      value={data?.unique_documents ?? 0}  sub="unique files"      color="cyan" />
        <StatCard icon={Activity}      label="Indexed Chunks" value={data?.total_chunks ?? 0}       sub="vector embeddings" color="purple" />
        <StatCard icon={MessageSquare} label="Total Queries"  value={data?.total_queries ?? 0}      sub="all time"          color="emerald" />
        <StatCard icon={Users}         label="Sessions"       value={data?.total_sessions ?? 0}     sub="conversations"     color="yellow" />
      </div>

      {/* Feedback + Cost row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={ThumbsUp}
          label="Positive Feedback"
          value={feedback?.positive ?? 0}
          sub={feedback?.total ? `${Math.round((feedback.positive_rate ?? 0) * 100)}% approval` : 'no feedback yet'}
          color="emerald"
        />
        <StatCard
          icon={ThumbsDown}
          label="Negative Feedback"
          value={feedback?.negative ?? 0}
          sub={`${feedback?.total ?? 0} total ratings`}
          color="rose"
        />
        <StatCard
          icon={DollarSign}
          label="Total Cost"
          value={costs ? `$${costs.total_cost_usd.toFixed(4)}` : '—'}
          sub="OpenAI API spend"
          color="orange"
        />
        <StatCard
          icon={Cpu}
          label="Tokens Used"
          value={costs ? `${((costs.total_input_tokens + costs.total_output_tokens) / 1000).toFixed(1)}k` : '—'}
          sub={costs ? `${costs.total_input_tokens.toLocaleString()} in / ${costs.total_output_tokens.toLocaleString()} out` : ''}
          color="purple"
        />
      </div>

      {/* Feedback satisfaction bar */}
      {(feedback?.total ?? 0) > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass border border-white/8 rounded-2xl p-5"
        >
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-slate-200">User Satisfaction</h3>
            <span className="text-xs text-slate-500">{feedback!.total} ratings</span>
          </div>
          <div className="w-full h-3 rounded-full bg-white/5 overflow-hidden">
            <div
              className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-cyan-500 transition-all duration-700"
              style={{ width: `${Math.round((feedback!.positive_rate ?? 0) * 100)}%` }}
            />
          </div>
          <div className="flex justify-between mt-2 text-xs text-slate-600">
            <span className="text-emerald-400">{Math.round((feedback!.positive_rate ?? 0) * 100)}% positive</span>
            <span className="text-rose-400">{100 - Math.round((feedback!.positive_rate ?? 0) * 100)}% negative</span>
          </div>
        </motion.div>
      )}

      {/* Activity chart */}
      {activityData.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="glass border border-white/8 rounded-2xl p-5"
        >
          <h3 className="text-sm font-semibold text-slate-200 mb-4">Query Activity (last 14 days)</h3>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={activityData} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
              <defs>
                <linearGradient id="gradQ" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={CHART_COLORS.primary} stopOpacity={0.3} />
                  <stop offset="95%" stopColor={CHART_COLORS.primary} stopOpacity={0} />
                </linearGradient>
                <linearGradient id="gradS" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={CHART_COLORS.secondary} stopOpacity={0.3} />
                  <stop offset="95%" stopColor={CHART_COLORS.secondary} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke={CHART_COLORS.grid} strokeDasharray="3 3" />
              <XAxis dataKey="date" tick={{ fill: '#475569', fontSize: 10 }} tickLine={false} />
              <YAxis tick={{ fill: '#475569', fontSize: 10 }} tickLine={false} axisLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Area type="monotone" dataKey="queries"  stroke={CHART_COLORS.primary}   fill="url(#gradQ)" strokeWidth={2} name="Queries" />
              <Area type="monotone" dataKey="sessions" stroke={CHART_COLORS.secondary} fill="url(#gradS)" strokeWidth={2} name="Sessions" />
            </AreaChart>
          </ResponsiveContainer>
        </motion.div>
      )}

      {/* Cost by model */}
      {modelCostData.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="glass border border-white/8 rounded-2xl p-5"
        >
          <h3 className="text-sm font-semibold text-slate-200 mb-4">Cost by Model</h3>
          <ResponsiveContainer width="100%" height={160}>
            <BarChart data={modelCostData} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
              <CartesianGrid stroke={CHART_COLORS.grid} strokeDasharray="3 3" />
              <XAxis dataKey="model" tick={{ fill: '#475569', fontSize: 11 }} tickLine={false} />
              <YAxis tick={{ fill: '#475569', fontSize: 11 }} tickLine={false} axisLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="cost" fill="#f97316" radius={[4, 4, 0, 0]} name="Cost ($)" />
            </BarChart>
          </ResponsiveContainer>
        </motion.div>
      )}

      {/* Session distribution */}
      {distData.some((d) => d.count > 0) && (
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="glass border border-white/8 rounded-2xl p-5"
        >
          <h3 className="text-sm font-semibold text-slate-200 mb-4">Messages per Session</h3>
          <ResponsiveContainer width="100%" height={160}>
            <BarChart data={distData} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
              <CartesianGrid stroke={CHART_COLORS.grid} strokeDasharray="3 3" />
              <XAxis dataKey="range" tick={{ fill: '#475569', fontSize: 11 }} tickLine={false} />
              <YAxis tick={{ fill: '#475569', fontSize: 11 }} tickLine={false} axisLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="count" fill={CHART_COLORS.secondary} radius={[4, 4, 0, 0]} name="Sessions" />
            </BarChart>
          </ResponsiveContainer>
        </motion.div>
      )}

      {/* Recent sessions table */}
      {(data?.sessions?.length ?? 0) > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="glass border border-white/8 rounded-2xl overflow-hidden"
        >
          <div className="px-5 py-4 border-b border-white/5">
            <h3 className="text-sm font-semibold text-slate-200">Recent Sessions</h3>
          </div>
          <div className="divide-y divide-white/5">
            {data!.sessions.slice(0, 8).map((s) => (
              <div key={s.session_id} className="px-5 py-3 flex items-center justify-between hover:bg-white/2 transition-colors">
                <div>
                  <p className="text-xs text-slate-300 font-mono">{s.session_id.slice(0, 16)}…</p>
                  <p className="text-xs text-slate-600 mt-0.5">
                    {s.last_activity
                      ? formatDistanceToNow(new Date(s.last_activity), { addSuffix: true })
                      : '—'}
                  </p>
                </div>
                <span className="px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 text-xs font-mono">
                  {s.message_count} msg
                </span>
              </div>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  )
}
