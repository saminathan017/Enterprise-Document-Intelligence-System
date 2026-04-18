import { useEffect } from 'react'
import { useStore } from '@/store/useStore'
import Background3D from '@/components/Background3D'
import Sidebar from '@/components/Sidebar'
import Header from '@/components/Header'
import ChatView from '@/components/ChatView'
import DocumentsView from '@/components/DocumentsView'
import AnalyticsView from '@/components/AnalyticsView'
import GraphView from '@/components/GraphView'
import PipelineView from '@/components/PipelineView'
import CommandPalette from '@/components/CommandPalette'
import { AnimatePresence, motion } from 'framer-motion'

const viewMap = {
  chat: ChatView,
  documents: DocumentsView,
  analytics: AnalyticsView,
  graph: GraphView,
  pipeline: PipelineView,
} as const

export default function App() {
  const { activeView, commandPaletteOpen, setCommandPaletteOpen, sidebarOpen } = useStore()

  // Global keyboard shortcut: Cmd/Ctrl+K → command palette
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setCommandPaletteOpen(true)
      }
      if (e.key === 'Escape') setCommandPaletteOpen(false)
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [setCommandPaletteOpen])

  const ActiveView = viewMap[activeView]

  return (
    <div className="flex h-screen w-screen overflow-hidden">
      {/* Animated 3D neural network background */}
      <Background3D />

      {/* Sidebar */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.div
            key="sidebar"
            initial={{ x: -280, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: -280, opacity: 0 }}
            transition={{ type: 'spring', stiffness: 300, damping: 30 }}
            className="flex-shrink-0"
          >
            <Sidebar />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main content */}
      <div className="flex flex-col flex-1 min-w-0 h-full">
        <Header />
        <main className="flex-1 min-h-0 overflow-hidden">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeView}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
              className="h-full"
            >
              <ActiveView />
            </motion.div>
          </AnimatePresence>
        </main>
      </div>

      {/* Command palette overlay */}
      <AnimatePresence>
        {commandPaletteOpen && <CommandPalette />}
      </AnimatePresence>
    </div>
  )
}
