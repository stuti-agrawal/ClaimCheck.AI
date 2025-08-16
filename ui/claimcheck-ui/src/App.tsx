import { useEffect } from 'react'
import { Header } from '@/components/Header'
import { UploadPanel } from '@/components/UploadPanel'
import { TranscriptPanel } from '@/components/TranscriptPanel'
import { SettingsPanel } from '@/components/SettingsPanel'
import { Stepper } from '@/components/Stepper'
import { ResultsSummary } from '@/components/ResultsSummary'
import { ClaimsTable } from '@/components/ClaimsTable'
import { EvidenceDrawer } from '@/components/EvidenceDrawer'
import { TranscriptViewer } from '@/components/TranscriptViewer'
import { RunHistory } from '@/components/RunHistory'
import { useAppStore } from '@/store/appStore'

export default function App() {
  const currentRun = useAppStore((s) => s.runs.find((r) => r.id === s.currentRunId))
  const loadFromStorage = useAppStore((s) => s.loadFromStorage)

  useEffect(() => {
    loadFromStorage()
  }, [loadFromStorage])

  return (
    <div className="min-h-full">
      <Header />
      <main className="px-4 sm:px-6 lg:px-8 py-6 max-w-7xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <section className="lg:col-span-5 space-y-6" aria-label="Input panel and run history">
            <div className="bg-card text-card-foreground rounded-lg border">
              <div className="p-4">
                <SettingsTabs />
              </div>
            </div>
            <RunHistory />
          </section>

          <section className="lg:col-span-7 space-y-4" aria-label="Results panel">
            <Stepper />
            {currentRun?.report ? (
              <div className="space-y-4">
                <ResultsSummary />
                <ClaimsTable />
                <TranscriptViewer />
                <EvidenceDrawer />
              </div>
            ) : (
              <EmptyState />)
            }
          </section>
        </div>
      </main>
    </div>
  )
}

function SettingsTabs() {
  // Simple tabs without external lib for accessibility
  // 0: Upload, 1: Transcript, 2: Settings
  const tab = useAppStore((s) => s.ui.tab)
  const setTab = useAppStore((s) => s.setTab)

  return (
    <div role="tablist" aria-label="Input tabs" className="w-full">
      <div className="flex gap-2 border-b pb-2">
        <button
          role="tab"
          aria-selected={tab === 0}
          className={`px-3 py-2 rounded-md text-sm font-medium ${tab === 0 ? 'bg-accent text-accent-foreground' : 'hover:bg-muted'}`}
          onClick={() => setTab(0)}
        >
          Upload Audio
        </button>
        <button
          role="tab"
          aria-selected={tab === 1}
          className={`px-3 py-2 rounded-md text-sm font-medium ${tab === 1 ? 'bg-accent text-accent-foreground' : 'hover:bg-muted'}`}
          onClick={() => setTab(1)}
        >
          Paste Transcript
        </button>
        <button
          role="tab"
          aria-selected={tab === 2}
          className={`px-3 py-2 rounded-md text-sm font-medium ${tab === 2 ? 'bg-accent text-accent-foreground' : 'hover:bg-muted'}`}
          onClick={() => setTab(2)}
        >
          KB & Settings
        </button>
      </div>

      <div className="mt-4">
        {tab === 0 && <UploadPanel />}
        {tab === 1 && <TranscriptPanel />}
        {tab === 2 && <SettingsPanel />}
      </div>
    </div>
  )
}

function EmptyState() {
  return (
    <div className="bg-card text-card-foreground rounded-lg border p-8">
      <h2 className="text-lg font-semibold">Welcome to ClaimCheck.AI</h2>
      <p className="text-sm text-muted-foreground mt-2">
        Upload an audio file or paste a transcript to verify claims against your knowledge base. Use the sample data to explore the UI.
      </p>
      <div className="mt-4">
        <SampleDataButton />
      </div>
    </div>
  )
}

function SampleDataButton() {
  const loadSample = useAppStore((s) => s.loadSample)
  return (
    <button onClick={loadSample} className="inline-flex items-center gap-2 px-3 py-2 rounded-md bg-primary text-primary-foreground hover:opacity-90">
      Use Sample Data
    </button>
  )
} 