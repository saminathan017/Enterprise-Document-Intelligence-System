import { useState } from 'react'
import { Download, Check } from 'lucide-react'
import { motion } from 'framer-motion'
import { useStore } from '@/store/useStore'
import { format } from 'date-fns'
import type { Message } from '@/types'

function renderMessage(msg: Message): string {
  const role  = msg.role === 'user' ? '👤 You' : '🤖 AI Analyst'
  const time  = format(new Date(msg.createdAt), 'HH:mm:ss')
  const body  = msg.content
  const cites = (msg.citations ?? [])
    .map((c, i) => `  [${i + 1}] ${c.source} — relevance ${Math.round(c.score * 100)}%`)
    .join('\n')

  return [
    `### ${role}  ·  ${time}`,
    '',
    body,
    cites ? '\n**Sources:**\n' + cites : '',
  ]
    .filter((l) => l !== undefined)
    .join('\n')
}

export default function ExportButton() {
  const { sessionId, getMessages } = useStore()
  const [done, setDone] = useState(false)

  const handleExport = () => {
    const messages = getMessages(sessionId)
    if (!messages.length) return

    const dateStr = format(new Date(), 'yyyy-MM-dd HH:mm')
    const header = [
      `# Enterprise Document Intelligence — Conversation Export`,
      `**Date:** ${dateStr}`,
      `**Session:** ${sessionId.slice(0, 16)}…`,
      `**Messages:** ${messages.length}`,
      '',
      '---',
      '',
    ].join('\n')

    const body = messages.map(renderMessage).join('\n\n---\n\n')
    const markdown = header + body

    // Open print dialog with formatted HTML
    const win = window.open('', '_blank', 'width=900,height=700')
    if (!win) return

    win.document.write(`<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8"/>
  <title>Chat Export — ${dateStr}</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 800px; margin: 40px auto; color: #1e293b; line-height: 1.6; }
    h1   { color: #0f172a; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px; }
    h3   { color: #475569; font-size: 0.9rem; margin-bottom: 4px; }
    hr   { border: none; border-top: 1px solid #e2e8f0; margin: 24px 0; }
    pre  { background: #f8fafc; padding: 12px; border-radius: 6px; overflow-x: auto; font-size: 0.85em; }
    code { background: #f1f5f9; padding: 2px 5px; border-radius: 3px; font-size: 0.9em; }
    blockquote { border-left: 3px solid #cbd5e1; margin: 0; padding-left: 16px; color: #64748b; }
    @media print { body { margin: 20px; } }
  </style>
</head>
<body>
  <script>
    const md = ${JSON.stringify(markdown)};
    // Simple markdown-to-HTML (headings, bold, code, hr)
    document.body.innerHTML = md
      .replace(/^### (.+)/gm, '<h3>$1</h3>')
      .replace(/^## (.+)/gm,  '<h2>$1</h2>')
      .replace(/^# (.+)/gm,   '<h1>$1</h1>')
      .replace(/\\*\\*(.+?)\\*\\*/g, '<strong>$1</strong>')
      .replace(/\`([^\`]+)\`/g, '<code>$1</code>')
      .replace(/^---$/gm, '<hr/>')
      .replace(/\\n/g, '<br/>');
    window.print();
  </script>
</body>
</html>`)
    win.document.close()

    setDone(true)
    setTimeout(() => setDone(false), 2500)
  }

  return (
    <motion.button
      whileTap={{ scale: 0.9 }}
      onClick={handleExport}
      title="Export conversation to PDF"
      className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs text-slate-500 hover:text-slate-200 hover:bg-white/5 transition-all"
    >
      {done ? (
        <Check size={13} className="text-emerald-400" />
      ) : (
        <Download size={13} />
      )}
      {done ? 'Exported' : 'Export PDF'}
    </motion.button>
  )
}
