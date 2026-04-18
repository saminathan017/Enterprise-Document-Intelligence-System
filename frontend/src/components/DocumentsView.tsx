import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Upload, FileText, Trash2, CheckCircle,
  AlertCircle, FileType, Database
} from 'lucide-react'
import { listDocuments, uploadDocument, deleteDocument } from '@/api/client'
import { useStore } from '@/store/useStore'
import { clsx } from 'clsx'

interface UploadState {
  name: string
  status: 'uploading' | 'done' | 'error'
  message?: string
  chunks?: number
}

const FILE_TYPE_COLORS: Record<string, string> = {
  pdf: 'text-red-400 bg-red-500/10',
  txt: 'text-blue-400 bg-blue-500/10',
  md:  'text-red-400 bg-red-500/10',
}

function humanSize(bytes: number) {
  if (bytes === 0) return '—'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1_048_576) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1_048_576).toFixed(1)} MB`
}

export default function DocumentsView() {
  const { sessionId } = useStore()
  const qc = useQueryClient()
  const [uploads, setUploads] = useState<UploadState[]>([])

  const { data, isLoading } = useQuery({
    queryKey: ['documents'],
    queryFn: listDocuments,
    refetchInterval: 10_000,
  })

  const onDrop = useCallback(
    async (accepted: File[]) => {
      for (const file of accepted) {
        setUploads((prev) => [{ name: file.name, status: 'uploading' }, ...prev])
        try {
          const res = await uploadDocument(file, sessionId)
          setUploads((prev) =>
            prev.map((u) =>
              u.name === file.name
                ? { ...u, status: 'done', message: `${res.chunks_created} chunks`, chunks: res.chunks_created }
                : u
            )
          )
          qc.invalidateQueries({ queryKey: ['documents'] })
          qc.invalidateQueries({ queryKey: ['health'] })
        } catch (err) {
          const msg = err instanceof Error ? err.message : 'Upload failed'
          setUploads((prev) =>
            prev.map((u) =>
              u.name === file.name ? { ...u, status: 'error', message: msg } : u
            )
          )
        }
      }
    },
    [sessionId, qc]
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'], 'text/plain': ['.txt'], 'text/markdown': ['.md'] },
    maxSize: 50 * 1024 * 1024,
  })

  const handleDelete = async (docId: string) => {
    try {
      await deleteDocument(docId)
      qc.invalidateQueries({ queryKey: ['documents'] })
      qc.invalidateQueries({ queryKey: ['health'] })
    } catch { /* ignore */ }
  }

  const docs = data?.documents ?? []

  return (
    <div className="h-full overflow-y-auto px-6 py-6 space-y-6">
      {/* Stats row */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: 'Documents', value: docs.length, icon: FileText, color: 'cyan' },
          { label: 'Total Chunks', value: docs.reduce((a, d) => a + d.total_chunks, 0), icon: Database, color: 'red' },
          { label: 'Uploading', value: uploads.filter((u) => u.status === 'uploading').length, icon: Upload, color: 'yellow' },
        ].map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="glass border border-white/8 rounded-2xl px-5 py-4 flex items-center gap-4">
            <div className={clsx(
              'w-10 h-10 rounded-xl flex items-center justify-center',
              color === 'cyan' ? 'bg-cyan-500/15' : color === 'red' ? 'bg-red-500/15' : 'bg-yellow-500/15'
            )}>
              <Icon size={18} className={
                color === 'cyan' ? 'text-cyan-400' : color === 'red' ? 'text-red-400' : 'text-yellow-400'
              } />
            </div>
            <div>
              <p className="text-2xl font-semibold text-white">{value}</p>
              <p className="text-xs text-slate-500">{label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Drop zone */}
      <div
        {...getRootProps()}
        className={clsx(
          'border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition-all duration-200',
          isDragActive
            ? 'border-cyan-500/60 bg-cyan-500/5 scale-[1.01]'
            : 'border-white/10 hover:border-white/20 hover:bg-white/2'
        )}
      >
        <input {...getInputProps()} />
        <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-cyan-500/10 to-red-500/10 border border-white/10 flex items-center justify-center mx-auto mb-4">
          <Upload size={24} className={isDragActive ? 'text-cyan-400' : 'text-slate-500'} />
        </div>
        <p className="text-slate-300 font-medium mb-1">
          {isDragActive ? 'Drop files here' : 'Drag & drop files'}
        </p>
        <p className="text-sm text-slate-600">
          PDF, TXT, or Markdown · Up to 50 MB per file
        </p>
      </div>

      {/* Upload progress */}
      <AnimatePresence>
        {uploads.map((u) => (
          <motion.div
            key={u.name}
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="glass border border-white/8 rounded-xl px-4 py-3 flex items-center gap-3"
          >
            {u.status === 'uploading' ? (
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                className="w-4 h-4 border-2 border-cyan-500/30 border-t-cyan-400 rounded-full flex-shrink-0"
              />
            ) : u.status === 'done' ? (
              <CheckCircle size={16} className="text-emerald-400 flex-shrink-0" />
            ) : (
              <AlertCircle size={16} className="text-red-400 flex-shrink-0" />
            )}
            <span className="text-sm text-slate-300 truncate flex-1">{u.name}</span>
            <span className={clsx(
              'text-xs',
              u.status === 'done' ? 'text-emerald-400' :
              u.status === 'error' ? 'text-red-400' : 'text-slate-500'
            )}>
              {u.status === 'uploading' ? 'Processing…' : u.message}
            </span>
          </motion.div>
        ))}
      </AnimatePresence>

      {/* Document list */}
      <div>
        <h3 className="text-sm font-semibold text-slate-300 mb-3">
          Indexed Documents
          {docs.length > 0 && <span className="ml-2 text-slate-600 font-normal">({docs.length})</span>}
        </h3>

        {isLoading ? (
          <div className="space-y-3">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="glass border border-white/5 rounded-xl h-16 animate-pulse" />
            ))}
          </div>
        ) : docs.length === 0 ? (
          <div className="text-center py-12 text-slate-600">
            <FileType size={32} className="mx-auto mb-3 opacity-30" />
            <p className="text-sm">No documents indexed yet. Upload your first file above.</p>
          </div>
        ) : (
          <div className="space-y-2">
            {docs.map((doc) => {
              const ext = doc.source.split('.').pop()?.toLowerCase() ?? 'txt'
              const typeStyle = FILE_TYPE_COLORS[ext] ?? 'text-slate-400 bg-slate-500/10'
              return (
                <motion.div
                  key={doc.document_id}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="group glass border border-white/8 rounded-xl px-4 py-3 flex items-center gap-4 hover:border-white/15 transition-all"
                >
                  <div className={clsx('px-2 py-1 rounded-lg text-[11px] font-mono font-medium uppercase flex-shrink-0', typeStyle)}>
                    {ext}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-slate-200 font-medium truncate">{doc.source}</p>
                    <p className="text-xs text-slate-600 mt-0.5">
                      {doc.total_chunks} chunks · {humanSize(doc.file_size_bytes)}
                    </p>
                  </div>
                  <button
                    onClick={() => handleDelete(doc.document_id || doc.source)}
                    className="opacity-0 group-hover:opacity-100 p-1.5 rounded-lg hover:bg-red-500/10 hover:text-red-400 text-slate-600 transition-all"
                  >
                    <Trash2 size={14} />
                  </button>
                </motion.div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
