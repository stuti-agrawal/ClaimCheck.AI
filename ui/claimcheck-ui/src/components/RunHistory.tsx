import { useAppStore } from '@/store/appStore'
import { History } from 'lucide-react'

export function RunHistory() {
  const runs = useAppStore((s) => s.runs)
  const selectRun = useAppStore((s) => s.selectRun)
  const currentRunId = useAppStore((s) => s.currentRunId)

  return (
    <div className="bg-card text-card-foreground rounded-lg border">
      <div className="p-4 border-b flex items-center gap-2">
        <History size={16} />
        <h3 className="font-medium">Run History</h3>
      </div>
      <ul className="divide-y" role="list" aria-label="Recent runs">
        {runs.length === 0 && (
          <li className="p-4 text-sm text-muted-foreground">No runs yet</li>
        )}
        {runs.map((r) => (
          <li key={r.id} className="p-3">
            <button
              className={`w-full text-left px-2 py-2 rounded-md hover:bg-muted ${currentRunId === r.id ? 'bg-muted' : ''}`}
              onClick={() => selectRun(r.id)}
            >
              <div className="text-sm font-medium">{new Date(r.startedAt).toLocaleString()}</div>
              <div className="text-xs text-muted-foreground">{r.inputKind}</div>
              {r.error && <div className="mt-1 text-xs text-red-600">{r.error}</div>}
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
} 