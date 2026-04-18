// ── Domain types ──────────────────────────────────────────────────────────────

export type MessageRole = 'user' | 'assistant'

export interface Citation {
  source: string
  chunk_id?: string
  score: number
  excerpt: string
}

export interface Message {
  id: string
  role: MessageRole
  content: string
  citations?: Citation[]
  processingMs?: number
  createdAt: number
  isStreaming?: boolean
  pipelineSteps?: PipelineStep[]
}

export interface Session {
  session_id: string
  message_count: number
  created_at: string
  last_activity: string
  title: string
}

export interface Document {
  source: string
  document_id: string
  file_type: string
  total_chunks: number
  ingested_at: string
  file_size_bytes: number
}

export interface AnalyticsSummary {
  total_chunks: number
  unique_documents: number
  total_sessions: number
  total_queries: number
  sessions: SessionStat[]
}

export interface SessionStat {
  session_id: string
  message_count: number
  created_at: string
  last_activity: string
}

// ── Graph types ───────────────────────────────────────────────────────────────

export type EntityType =
  | 'person'
  | 'organization'
  | 'metric'
  | 'concept'
  | 'date'
  | 'location'

export interface GraphNode {
  id: string
  label: string
  type: EntityType | string
  sources?: string[]
}

export interface GraphEdge {
  id: string
  source: string
  target: string
  label: string
}

export interface KnowledgeGraph {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

// ── Streaming / pipeline types ─────────────────────────────────────────────────

export type PipelineStepName =
  | 'retrieval' | 'hyde' | 'context' | 'generation'
  | 'crag' | 'compression'

export type PipelineStatus = 'idle' | 'running' | 'done' | 'error' | 'skipped'

export interface PipelineStep {
  step: PipelineStepName
  status: PipelineStatus
  message?: string
  elapsed_ms?: number
  count?: number
  tokens?: number
}

export type SSEEvent =
  | { type: 'step' } & PipelineStep
  | { type: 'token'; content: string }
  | { type: 'citations'; citations: Citation[] }
  | { type: 'metrics'; faithfulness: number; processing_ms: number }
  | { type: 'done'; total_tokens?: number; elapsed_ms?: number; docs_used?: number }
  | { type: 'error'; message: string }

// ── UI state ──────────────────────────────────────────────────────────────────

export type View = 'chat' | 'documents' | 'analytics' | 'graph' | 'pipeline'

export type Model =
  | 'gpt-4o'
  | 'gpt-4o-mini'
  | 'gpt-4-turbo-preview'
  | 'gpt-4'
