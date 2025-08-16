import { useMemo } from 'react'
import { useAppStore } from '@/store/appStore'
import type { Evidence } from '@/lib/types'

export function EvidenceDrawer() {
  const run = useAppStore((s) => s.runs.find((r) => r.id === s.currentRunId))
  const isOpen = useAppStore((s) => s.ui.evidenceOpen)
  const claimId = useAppStore((s) => s.ui.selectedClaimId)
  const close = useAppStore((s) => s.closeEvidence)

  const claim = useMemo(() => run?.report?.claims.find((c) => c.id === claimId), [run, claimId])
  const verdict = useMemo(() => run?.report?.verdicts.find((v) => v.claim_id === claimId), [run, claimId])

  const evidences = useMemo(() => {
    if (!run?.report) return [] as Evidence[]
    const report = run.report

    // 1) Prefer cited evidence for this claim
    const citedIds = verdict?.citation_ids || []
    if (citedIds.length > 0) {
      const cited = report.evidence.filter((e) => citedIds.includes(e.doc_id))
      if (cited.length > 0) return cited
    }

    // 2) Fallback to per-claim retrieved evidence
    const byClaim = report.evidence_by_claim?.[claimId ?? ''] || []
    if (byClaim.length > 0) return byClaim

    // 3) Final fallback: top-scored global evidence
    const sorted = [...report.evidence].sort((a, b) => (b.score ?? 0) - (a.score ?? 0))
    return sorted.slice(0, 5)
  }, [run, verdict, claimId])

  if (!isOpen) return null

  return (
    <div role="dialog" aria-modal="true" className="fixed inset-0 z-50">
      <div className="absolute inset-0 bg-black/40" onClick={close} />
      <div className="absolute top-0 right-0 h-full w-full sm:w-[420px] bg-card text-card-foreground border-l shadow-xl overflow-auto" tabIndex={-1} aria-labelledby="evidence-title">
        <div className="p-4 border-b flex items-start justify-between">
          <h3 id="evidence-title" className="font-semibold pr-4">Evidence & Rationale</h3>
          <button className="text-sm px-2 py-1 rounded-md border hover:bg-muted" onClick={close}>Close</button>
        </div>
        <div className="p-4 space-y-4">
          {claim && (
            <div>
              <div className="text-xs text-muted-foreground">Claim</div>
              <div className="mt-1 text-sm">{claim.text}</div>
            </div>
          )}

          <div>
            <div className="text-xs text-muted-foreground">Top Evidence</div>
            <ul className="mt-2 space-y-3">
              {evidences.map((e, idx) => (
                <li key={`${e.doc_id}-${idx}`} className="rounded-md border p-3">
                  <div className="text-xs text-muted-foreground">{e.source || e.doc_id} • score {(e.score ?? 0).toFixed(2)}</div>
                  <div className="mt-1 text-sm whitespace-pre-wrap">{e.snippet}</div>
                  {e.metadata && (
                    <pre className="mt-2 text-xs text-muted-foreground whitespace-pre-wrap">{JSON.stringify(e.metadata, null, 2)}</pre>
                  )}
                </li>
              ))}
              {evidences.length === 0 && <li className="text-sm text-muted-foreground">No evidence</li>}
            </ul>
          </div>

          {verdict?.rationale && (
            <div>
              <div className="text-xs text-muted-foreground">Model Rationale</div>
              <div className="mt-1 text-sm whitespace-pre-wrap">{verdict.rationale}</div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
} 