import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { nanoid } from '@/store/nanoid'
import type { CallReport, InputKind, RunRecord, VerdictLabel } from '@/lib/types'
import { processAudio, processTranscript } from '@/lib/api'

export type StepKey = 'ASR' | 'Claims' | 'Retrieval' | 'Verification' | 'Summary'
export type StepStatus = 'idle' | 'running' | 'done' | 'error'

export type UIState = {
  tab: 0 | 1 | 2
  filter: 'all' | VerdictLabel
  evidenceOpen: boolean
  selectedClaimId?: string
}

type Store = {
  runs: RunRecord[]
  currentRunId?: string
  steps: Record<StepKey, StepStatus>
  ui: UIState
  setTab: (tab: 0 | 1 | 2) => void
  setFilter: (f: 'all' | VerdictLabel) => void
  openEvidence: (claimId: string) => void
  closeEvidence: () => void
  startRun: (kind: InputKind, payload: { file?: File; text?: string }) => Promise<void>
  loadSample: () => Promise<void>
  loadFromStorage: () => void
  selectRun: (id: string) => void
}

const initialSteps: Record<StepKey, StepStatus> = {
  ASR: 'idle',
  Claims: 'idle',
  Retrieval: 'idle',
  Verification: 'idle',
  Summary: 'idle',
}

export const useAppStore = create<Store>()(
  persist(
    (set, get) => ({
      runs: [],
      currentRunId: undefined,
      steps: initialSteps,
      ui: { tab: 0, filter: 'all', evidenceOpen: false },
      setTab: (tab) => set((s) => ({ ui: { ...s.ui, tab } })),
      setFilter: (filter) => set((s) => ({ ui: { ...s.ui, filter } })),
      openEvidence: (selectedClaimId) => set((s) => ({ ui: { ...s.ui, evidenceOpen: true, selectedClaimId } })),
      closeEvidence: () => set((s) => ({ ui: { ...s.ui, evidenceOpen: false, selectedClaimId: undefined } })),

      async startRun(kind, payload) {
        const id = nanoid()
        const startedAt = Date.now()
        const newRun: RunRecord = { id, startedAt, inputKind: kind }
        set((s) => ({ runs: [newRun, ...s.runs].slice(0, 5), currentRunId: id }))

        // optimistic step progression
        const audio = kind === 'audio'
        set({ steps: {
          ASR: audio ? 'running' : 'done',
          Claims: 'idle',
          Retrieval: 'idle',
          Verification: 'idle',
          Summary: 'idle',
        } })

        try {
          let report: CallReport
          if (kind === 'audio' && payload.file) {
            report = await processAudio(payload.file)
          } else if (kind === 'transcript' && payload.text) {
            report = await processTranscript(payload.text)
          } else {
            throw new Error('Missing input')
          }

          // set done
          set({ steps: { ASR: audio ? 'done' : 'done', Claims: 'done', Retrieval: 'done', Verification: 'done', Summary: 'done' } })
          set((s) => ({ runs: s.runs.map((r) => (r.id === id ? { ...r, report } : r)) }))
        } catch (err: any) {
          set({ steps: { ...initialSteps, ASR: audio ? 'error' : 'done', Claims: 'error' } })
          const message = err?.response?.data?.detail || err?.message || 'Failed to process request'
          set((s) => ({ runs: s.runs.map((r) => (r.id === id ? { ...r, error: message } : r)) }))
        }
      },

      async loadSample() {
        const id = nanoid()
        const startedAt = Date.now()
        const newRun: RunRecord = { id, startedAt, inputKind: 'sample' }
        set((s) => ({ runs: [newRun, ...s.runs].slice(0, 5), currentRunId: id }))
        set({ steps: { ASR: 'done', Claims: 'done', Retrieval: 'done', Verification: 'done', Summary: 'done' } })
        const data = await import('@/mocks/sampleReport.json')
        const report = data.default
        set((s) => ({ runs: s.runs.map((r) => (r.id === id ? { ...r, report } : r)) }))
      },

      loadFromStorage() {
        // noop: handled by persist middleware rehydration
      },

      selectRun(id) {
        set({ currentRunId: id })
      },
    }),
    {
      name: 'cc_runs',
      partialize: (s) => ({ runs: s.runs, currentRunId: s.currentRunId }),
    }
  )
) 