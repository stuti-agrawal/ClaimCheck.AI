import { useState } from 'react'
import { FileText, Play } from 'lucide-react'
import { useAppStore } from '@/store/appStore'
import { wordCount } from '@/lib/utils'

const SAMPLE = `Agent: Thanks for joining. We saw improved adoption this quarter.\nCustomer: We plan to expand to 3 more teams next month.\nAgent: Pricing will remain the same.\nCustomer: If support SLAs slip again, we may churn.`

export function TranscriptPanel() {
  const [text, setText] = useState('')
  const startRun = useAppStore((s) => s.startRun)

  function loadSample() {
    setText(SAMPLE)
  }

  return (
    <div className="space-y-4" aria-label="Paste transcript">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <FileText size={16} /> Paste call transcript
      </div>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        rows={10}
        className="w-full rounded-md border bg-background p-3 outline-none focus:ring-2 focus:ring-ring"
        placeholder="Paste transcript here..."
      />
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span>Word count: {wordCount(text)}</span>
        <button onClick={loadSample} className="underline hover:no-underline">
          Use sample text
        </button>
      </div>
      <div className="flex justify-end">
        <button
          disabled={!text.trim()}
          onClick={() => startRun('transcript', { text })}
          className={`inline-flex items-center gap-2 px-4 py-2 rounded-md ${!text.trim() ? 'bg-muted text-muted-foreground' : 'bg-primary text-primary-foreground hover:opacity-90'}`}
        >
          <Play size={16} /> Run
        </button>
      </div>
    </div>
  )
} 