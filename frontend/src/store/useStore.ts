import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Message, Session, Document, View, Model } from '@/types'

interface AppState {
  // Navigation
  activeView: View
  setActiveView: (v: View) => void

  // Session
  sessionId: string
  sessions: Session[]
  setSessionId: (id: string) => void
  setSessions: (sessions: Session[]) => void

  // Messages (per session)
  messagesBySession: Record<string, Message[]>
  addMessage: (sessionId: string, msg: Message) => void
  updateMessage: (sessionId: string, msgId: string, patch: Partial<Message>) => void
  clearMessages: (sessionId: string) => void
  getMessages: (sessionId: string) => Message[]

  // Documents
  documents: Document[]
  setDocuments: (docs: Document[]) => void

  // Model / settings
  model: Model
  setModel: (m: Model) => void
  useHyde: boolean
  setUseHyde: (v: boolean) => void
  topK: number
  setTopK: (k: number) => void

  // UI
  sidebarOpen: boolean
  toggleSidebar: () => void
  commandPaletteOpen: boolean
  setCommandPaletteOpen: (v: boolean) => void
}

export const useStore = create<AppState>()(
  persist(
    (set, get) => ({
      // Navigation
      activeView: 'chat',
      setActiveView: (v) => set({ activeView: v }),

      // Session
      sessionId: crypto.randomUUID(),
      sessions: [],
      setSessionId: (id) => set({ sessionId: id }),
      setSessions: (sessions) => set({ sessions }),

      // Messages
      messagesBySession: {},
      addMessage: (sessionId, msg) =>
        set((s) => ({
          messagesBySession: {
            ...s.messagesBySession,
            [sessionId]: [...(s.messagesBySession[sessionId] ?? []), msg],
          },
        })),
      updateMessage: (sessionId, msgId, patch) =>
        set((s) => ({
          messagesBySession: {
            ...s.messagesBySession,
            [sessionId]: (s.messagesBySession[sessionId] ?? []).map((m) =>
              m.id === msgId ? { ...m, ...patch } : m
            ),
          },
        })),
      clearMessages: (sessionId) =>
        set((s) => ({
          messagesBySession: { ...s.messagesBySession, [sessionId]: [] },
        })),
      getMessages: (sessionId) => get().messagesBySession[sessionId] ?? [],

      // Documents
      documents: [],
      setDocuments: (docs) => set({ documents: docs }),

      // Model
      model: 'gpt-4o',
      setModel: (m) => set({ model: m }),
      useHyde: false,
      setUseHyde: (v) => set({ useHyde: v }),
      topK: 5,
      setTopK: (k) => set({ topK: k }),

      // UI
      sidebarOpen: true,
      toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
      commandPaletteOpen: false,
      setCommandPaletteOpen: (v) => set({ commandPaletteOpen: v }),
    }),
    {
      name: 'ai-analyst-state',
      partialize: (s) => ({
        sessionId: s.sessionId,
        model: s.model,
        useHyde: s.useHyde,
        topK: s.topK,
        sidebarOpen: s.sidebarOpen,
        messagesBySession: s.messagesBySession,
      }),
    }
  )
)
