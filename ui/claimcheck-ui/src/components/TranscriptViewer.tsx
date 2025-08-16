import { useMemo, useState } from 'react'
import { useAppStore } from '@/store/appStore'

export function TranscriptViewer() {
  const [open, setOpen] = useState(false)
  const run = useAppStore((s) => s.runs.find((r) => r.id === s.currentRunId))

  const segments = useMemo(() => {
    const claims = run?.report?.claims ?? []
    // synthesize segments if none: group by speaker or fallback single block
    const text = (run?.report?.claim_table || []).map((c) => c.claim).join('\n')
    return [
      { speaker: 'Call', start: 0, end: 0, text, claims },
    ]
  }, [run])

  if (!run?.report) return null

  return (
    <div className="bg-card text-card-foreground rounded-lg border">
      <button className="w-full text-left p-4" onClick={() => setOpen((v) => !v)} aria-expanded={open}>
        <span className="font-medium">Transcript</span>
      </button>
      {open && (
        <div className="px-4 pb-4 space-y-4">
          {segments.map((seg, idx) => (
            <div key={idx} className="rounded-md border p-3">
              <div className="text-xs text-muted-foreground">{seg.speaker}</div>
              <div className="mt-1 text-sm whitespace-pre-wrap">
                {seg.text}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
} 