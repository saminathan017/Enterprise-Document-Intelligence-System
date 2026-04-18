import { useState, useRef, useCallback } from 'react'
import { motion } from 'framer-motion'
import { Mic, MicOff, Loader } from 'lucide-react'
import { clsx } from 'clsx'

interface Props {
  onTranscript: (text: string) => void
  disabled?: boolean
}

type VoiceState = 'idle' | 'listening' | 'processing'

// webkit prefix fallback for cross-browser Speech API
type AnySpeechRecognition = typeof SpeechRecognition
declare global {
  interface Window { webkitSpeechRecognition?: AnySpeechRecognition }
}

export default function VoiceInput({ onTranscript, disabled }: Props) {
  const [state, setState] = useState<VoiceState>('idle')
  const recogRef = useRef<SpeechRecognition | null>(null)

  const isSupported =
    typeof window !== 'undefined' &&
    (!!window.SpeechRecognition || !!window.webkitSpeechRecognition)

  const start = useCallback(() => {
    if (!isSupported || disabled) return
    const SpeechRec = window.SpeechRecognition ?? window.webkitSpeechRecognition
    if (!SpeechRec) return

    const rec = new SpeechRec()
    rec.lang             = 'en-US'
    rec.continuous       = false
    rec.interimResults   = true
    rec.maxAlternatives  = 1

    rec.onstart  = () => setState('listening')
    rec.onend    = () => setState('idle')
    rec.onerror  = () => setState('idle')

    rec.onresult = (e: SpeechRecognitionEvent) => {
      const transcript = Array.from(e.results)
        .map((r: SpeechRecognitionResult) => r[0].transcript)
        .join('')

      if (e.results[e.results.length - 1].isFinal) {
        setState('processing')
        onTranscript(transcript)
        setTimeout(() => setState('idle'), 400)
      }
    }

    rec.start()
    recogRef.current = rec
  }, [isSupported, disabled, onTranscript])

  const stop = useCallback(() => {
    recogRef.current?.stop()
    setState('idle')
  }, [])

  if (!isSupported) return null

  return (
    <motion.button
      whileTap={{ scale: 0.9 }}
      onClick={state === 'listening' ? stop : start}
      disabled={disabled || state === 'processing'}
      title={state === 'listening' ? 'Stop recording' : 'Voice input'}
      className={clsx(
        'p-1.5 rounded-lg transition-all duration-200',
        state === 'listening'
          ? 'bg-red-500/20 text-red-400 border border-red-500/30'
          : state === 'processing'
          ? 'text-cyan-400 opacity-60'
          : 'text-slate-500 hover:text-cyan-400 hover:bg-white/5'
      )}
    >
      {state === 'listening' ? (
        <motion.div
          animate={{ scale: [1, 1.2, 1] }}
          transition={{ repeat: Infinity, duration: 1 }}
        >
          <MicOff size={15} />
        </motion.div>
      ) : state === 'processing' ? (
        <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1, ease: 'linear' }}>
          <Loader size={15} />
        </motion.div>
      ) : (
        <Mic size={15} />
      )}
    </motion.button>
  )
}
