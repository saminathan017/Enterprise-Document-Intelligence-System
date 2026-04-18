import { useEffect, useRef, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { buildKnowledgeGraph } from '@/api/client'
import { Share2, RefreshCw, Info } from 'lucide-react'
import type { GraphNode } from '@/types'
import cytoscape from 'cytoscape'

const TYPE_COLORS: Record<string, string> = {
  person:       '#00d4ff',
  organization: '#ff1a1a',
  metric:       '#f59e0b',
  concept:      '#10b981',
  date:         '#64748b',
  location:     '#f43f5e',
}

const LAYOUT_OPTIONS: cytoscape.LayoutOptions = {
  name: 'cose',
  animate: true,
  animationDuration: 800,
  nodeRepulsion: () => 10000,
  idealEdgeLength: () => 80,
  fit: true,
  padding: 40,
}

export default function GraphView() {
  const cyRef = useRef<HTMLDivElement>(null)
  const cyInstance = useRef<cytoscape.Core | null>(null)
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null)
  const [stats, setStats] = useState({ nodes: 0, edges: 0 })

  const { mutate: loadGraph, isPending } = useMutation({
    mutationFn: () => buildKnowledgeGraph(40),
    onSuccess: (data) => {
      if (!cyRef.current) return
      setStats({ nodes: data.nodes.length, edges: data.edges.length })
      renderGraph(data.nodes, data.edges)
    },
  })

  function renderGraph(
    nodes: { id: string; label: string; type: string }[],
    edges: { id: string; source: string; target: string; label: string }[]
  ) {
    if (!cyRef.current) return

    if (cyInstance.current) {
      cyInstance.current.destroy()
    }

    const cy = cytoscape({
      container: cyRef.current,
      style: [
        {
          selector: 'node',
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          style: {
            'background-color': (ele: cytoscape.NodeSingular) =>
              TYPE_COLORS[ele.data('nodeType') as string] ?? '#8b5cf6',
            'label': 'data(label)',
            'color': '#e2e8f0',
            'font-size': '11px',
            'font-family': 'Inter, sans-serif',
            'text-valign': 'bottom',
            'text-halign': 'center',
            'text-margin-y': '6px',
            'width': '28px',
            'height': '28px',
            'border-width': '2px',
            'border-color': 'rgba(255,255,255,0.15)',
            'text-outline-width': '2px',
            'text-outline-color': '#050510',
          } as unknown as cytoscape.Css.Node,
        },
        {
          selector: 'node:selected',
          style: {
            'border-color': '#00d4ff',
            'border-width': '3px',
            'background-color': '#00d4ff',
          } as cytoscape.Css.Node,
        },
        {
          selector: 'edge',
          style: {
            'width': 1.5,
            'line-color': 'rgba(139,92,246,0.35)',
            'target-arrow-color': 'rgba(139,92,246,0.5)',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'label': 'data(label)',
            'font-size': '9px',
            'color': '#475569',
            'text-rotation': 'autorotate',
            'font-family': 'Inter, sans-serif',
            'text-outline-width': '2px',
            'text-outline-color': '#050510',
          } as cytoscape.Css.Edge,
        },
        {
          selector: 'edge:selected',
          style: {
            'line-color': '#00d4ff',
            'target-arrow-color': '#00d4ff',
          } as cytoscape.Css.Edge,
        },
      ],
      elements: {
        nodes: nodes.map((n) => ({
          data: { id: n.id, label: n.label, nodeType: n.type }
        })),
        edges: edges.map((e) => ({
          data: { id: e.id, source: e.source, target: e.target, label: e.label }
        })),
      },
      layout: LAYOUT_OPTIONS,
    })

    cy.on('tap', 'node', (evt) => {
      const n = evt.target
      const matched = nodes.find((x) => x.id === n.id())
      setSelectedNode(matched ?? null)
    })

    cy.on('tap', (evt) => {
      if (evt.target === cy) setSelectedNode(null)
    })

    cyInstance.current = cy
  }

  useEffect(() => {
    return () => { cyInstance.current?.destroy() }
  }, [])

  return (
    <div className="h-full flex flex-col">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-5 py-3 border-b border-white/5 flex-shrink-0">
        <div className="flex items-center gap-3">
          <Share2 size={16} className="text-cyan-400" />
          <span className="text-sm text-slate-300 font-medium">Knowledge Graph</span>
          {stats.nodes > 0 && (
            <span className="text-xs text-slate-600">
              {stats.nodes} entities · {stats.edges} relationships
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          {/* Legend */}
          <div className="hidden sm:flex items-center gap-3">
            {Object.entries(TYPE_COLORS).slice(0, 4).map(([type, color]) => (
              <div key={type} className="flex items-center gap-1.5">
                <div className="w-2.5 h-2.5 rounded-full" style={{ background: color }} />
                <span className="text-xs text-slate-600 capitalize">{type}</span>
              </div>
            ))}
          </div>
          <button
            onClick={() => loadGraph()}
            disabled={isPending}
            className="btn-primary flex items-center gap-1.5"
          >
            <RefreshCw size={13} className={isPending ? 'animate-spin' : ''} />
            {isPending ? 'Building…' : stats.nodes > 0 ? 'Refresh' : 'Build Graph'}
          </button>
        </div>
      </div>

      {/* Graph canvas + detail panel */}
      <div className="flex-1 relative overflow-hidden">
        {stats.nodes === 0 && !isPending ? (
          <div className="flex flex-col items-center justify-center h-full text-center px-8">
            <div className="w-16 h-16 rounded-2xl bg-red-500/10 border border-red-500/20 flex items-center justify-center mb-5">
              <Share2 size={28} className="text-red-400" />
            </div>
            <h3 className="text-lg font-semibold text-slate-200 mb-2">Entity Knowledge Graph</h3>
            <p className="text-sm text-slate-500 max-w-sm mb-6">
              Automatically extract entities and relationships from your documents using GPT-4.
            </p>
            <button onClick={() => loadGraph()} className="btn-primary">
              Build Knowledge Graph
            </button>
          </div>
        ) : isPending ? (
          <div className="flex flex-col items-center justify-center h-full gap-4">
            <div className="w-10 h-10 border-2 border-red-500/30 border-t-red-400 rounded-full animate-spin" />
            <p className="text-sm text-slate-500">Extracting entities with GPT-4…</p>
          </div>
        ) : null}

        {/* Cytoscape container */}
        <div ref={cyRef} className="absolute inset-0" style={{ background: 'transparent' }} />

        {/* Node detail panel */}
        {selectedNode && (
          <motion.div
            initial={{ opacity: 0, x: 16 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 16 }}
            className="absolute top-4 right-4 w-60 glass border border-white/10 rounded-2xl p-4 shadow-glass"
          >
            <div className="flex items-start justify-between mb-3">
              <div
                className="w-3 h-3 rounded-full mt-1 flex-shrink-0"
                style={{ background: TYPE_COLORS[selectedNode.type] ?? '#8b5cf6' }}
              />
              <div className="flex-1 px-3">
                <p className="text-sm font-semibold text-slate-200 leading-tight">{selectedNode.label}</p>
                <p className="text-xs text-slate-500 capitalize mt-0.5">{selectedNode.type}</p>
              </div>
              <button onClick={() => setSelectedNode(null)} className="text-slate-600 hover:text-slate-400">
                ✕
              </button>
            </div>
            {(selectedNode.sources?.length ?? 0) > 0 && (
              <div className="border-t border-white/5 pt-3">
                <p className="text-xs text-slate-600 mb-2 flex items-center gap-1">
                  <Info size={10} /> Found in
                </p>
                {selectedNode.sources!.map((src, i) => (
                  <p key={i} className="text-xs text-cyan-400 truncate">{src}</p>
                ))}
              </div>
            )}
          </motion.div>
        )}
      </div>
    </div>
  )
}
