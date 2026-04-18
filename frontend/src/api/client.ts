import type {
  Session,
  Document,
  AnalyticsSummary,
  KnowledgeGraph,
  SSEEvent,
  Citation,
} from '@/types'

const BASE = import.meta.env.VITE_API_BASE ?? ''

async function request<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail ?? `HTTP ${res.status}`)
  }
  return res.json()
}

// ── Health ────────────────────────────────────────────────────────────────────

export const healthCheck = () =>
  request<{ status: string; indexed_chunks: number; version: string }>('/health')

// ── Documents ─────────────────────────────────────────────────────────────────

export const listDocuments = () =>
  request<{ documents: Document[]; total: number }>('/api/v1/documents')

export async function uploadDocument(file: File, sessionId: string): Promise<{
  success: boolean
  document_id: string
  chunks_created: number
  filename: string
}> {
  const form = new FormData()
  form.append('file', file)
  form.append('session_id', sessionId)
  const res = await fetch(`${BASE}/api/v1/ingest`, { method: 'POST', body: form })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail ?? `HTTP ${res.status}`)
  }
  return res.json()
}

export const deleteDocument = (documentId: string) =>
  request<{ success: boolean; deleted_chunks: number }>(
    `/api/v1/documents/${encodeURIComponent(documentId)}`,
    { method: 'DELETE' }
  )

// ── Sessions ──────────────────────────────────────────────────────────────────

export const listSessions = () =>
  request<{ sessions: Session[] }>('/api/v1/sessions/list')

export const createSession = () =>
  request<{ session_id: string }>('/api/v1/session', {
    method: 'POST',
    body: JSON.stringify({ action: 'create' }),
  })

export const deleteSession = (sessionId: string) =>
  request<{ success: boolean }>(`/api/v1/sessions/${sessionId}`, {
    method: 'DELETE',
  })

// ── Analytics ─────────────────────────────────────────────────────────────────

export const getAnalytics = () =>
  request<AnalyticsSummary>('/api/v1/analytics')

// ── Feedback ──────────────────────────────────────────────────────────────────

export const getFeedbackSummary = () =>
  request<{ total: number; positive: number; negative: number; positive_rate: number }>(
    '/api/v1/feedback/summary'
  )

// ── Costs ─────────────────────────────────────────────────────────────────────

export const getCosts = () =>
  request<{
    total_input_tokens: number
    total_output_tokens: number
    total_cost_usd: number
    by_model: Record<string, { input: number; output: number; cost: number }>
  }>('/api/v1/costs')

// ── Knowledge Graph ───────────────────────────────────────────────────────────

export const buildKnowledgeGraph = (maxDocs = 30) =>
  request<KnowledgeGraph>('/api/v1/knowledge-graph', {
    method: 'POST',
    body: JSON.stringify({ max_docs: maxDocs }),
  })

// ── Standard (non-streaming) query ───────────────────────────────────────────

export const queryDocuments = (params: {
  query: string
  session_id: string
  top_k?: number
  use_web?: boolean
  make_table?: boolean
}) =>
  request<{
    success: boolean
    query: string
    answer: string
    citations: Citation[]
    session_id: string
    processing_time_ms: number
  }>('/api/v1/query', { method: 'POST', body: JSON.stringify(params) })

// ── Feedback submit ───────────────────────────────────────────────────────────

export const submitFeedback = (body: {
  session_id: string
  message_id: string
  query: string
  answer: string
  rating: 1 | -1
  model?: string
  processing_ms?: number
}) =>
  request<{ success: boolean; recorded: string }>('/api/v1/feedback', {
    method: 'POST',
    body: JSON.stringify(body),
  })

// ── SSE Streaming query ───────────────────────────────────────────────────────

export async function* streamQuery(params: {
  query: string
  session_id?: string
  top_k?: number
  model?: string
  use_hyde?: boolean
  use_crag?: boolean
  expand_parents?: boolean
  use_compression?: boolean
}): AsyncGenerator<SSEEvent> {
  const res = await fetch(`${BASE}/api/v1/stream/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  })

  if (!res.ok || !res.body) {
    throw new Error(`Stream failed: HTTP ${res.status}`)
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() ?? ''

    for (const line of lines) {
      const trimmed = line.trim()
      if (!trimmed.startsWith('data: ')) continue
      try {
        const event = JSON.parse(trimmed.slice(6)) as SSEEvent
        yield event
        if (event.type === 'done' || event.type === 'error') return
      } catch {
        // skip malformed lines
      }
    }
  }
}
