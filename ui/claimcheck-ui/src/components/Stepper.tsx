import { useAppStore, StepKey } from '@/store/appStore'
import { AudioWaveform, FileText, ListChecks, Search, ShieldCheck } from 'lucide-react'

const steps: { key: StepKey; label: string; icon: any }[] = [
  { key: 'ASR', label: 'ASR', icon: AudioWaveform },
  { key: 'Claims', label: 'Claims', icon: ListChecks },
  { key: 'Retrieval', label: 'Retrieval', icon: Search },
  { key: 'Verification', label: 'Verification', icon: ShieldCheck },
  { key: 'Summary', label: 'Summary', icon: FileText },
]

export function Stepper() {
  const state = useAppStore((s) => s.steps)
  return (
    <div className="bg-card text-card-foreground rounded-lg border p-3" role="group" aria-label="Pipeline status">
      <ol className="grid grid-cols-1 sm:grid-cols-5 gap-2">
        {steps.map(({ key, label, icon: Icon }) => {
          const status = state[key]
          return (
            <li key={key} className="flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${status === 'done' ? 'bg-green-500' : status === 'running' ? 'bg-blue-500 animate-pulse' : status === 'error' ? 'bg-red-500' : 'bg-muted-foreground/40'}`} />
              <span className="inline-flex items-center gap-2 text-sm">
                <Icon size={16} /> {label}
                {status === 'running' && <span className="ml-1 h-3 w-3 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" aria-label="Loading" />}
              </span>
            </li>
          )
        })}
      </ol>
    </div>
  )
} 