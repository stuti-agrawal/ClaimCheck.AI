import { useMemo, useState } from 'react'
import { useAppStore } from '@/store/appStore'
import type { VerdictLabel } from '@/lib/types'
import { confidencePercent, verdictColor } from '@/lib/utils'

export function ClaimsTable() {
  const run = useAppStore((s) => s.runs.find((r) => r.id === s.currentRunId))
  const filter = useAppStore((s) => s.ui.filter)
  const setFilter = useAppStore((s) => s.setFilter)
  const openEvidence = useAppStore((s) => s.openEvidence)

  const [sortAsc, setSortAsc] = useState<boolean>(false)

  const rows = useMemo(() => {
    if (!run?.report) return []
    const { claims, verdicts, evidence } = run.report
    const byClaim: Record<string, any> = {}
    for (const c of claims) byClaim[c.id] = { claim: c }
    for (const v of verdicts) byClaim[v.claim_id] = { ...(byClaim[v.claim_id] || {}), verdict: v }

    let data = Object.values(byClaim)
    if (filter !== 'all') {
      data = data.filter((r: any) => r.verdict?.label === filter)
    }
    data.sort((a: any, b: any) => (sortAsc ? (a.verdict?.confidence ?? 0) - (b.verdict?.confidence ?? 0) : (b.verdict?.confidence ?? 0) - (a.verdict?.confidence ?? 0)))

    return data.map((r: any) => {
      const evid = evidence.find((e) => e.doc_id === r.verdict?.best_evidence_id)
      return { ...r, evidence: evid }
    })
  }, [run, filter, sortAsc])

  if (!run?.report) return null

  const filters: ('all' | VerdictLabel)[] = ['all', 'supported', 'refuted', 'insufficient']

  return (
    <div className="bg-card text-card-foreground rounded-lg border">
      <div className="p-4 flex items-center justify-between">
        <h3 className="font-medium">Claims</h3>
        <div className="flex items-center gap-2">
          {filters.map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`text-xs px-2 py-1 rounded-md border ${filter === f ? 'bg-accent' : 'hover:bg-muted'}`}
            >
              {f}
            </button>
          ))}
          <button className="text-xs px-2 py-1 rounded-md border hover:bg-muted" onClick={() => setSortAsc((v) => !v)}>
            Sort by confidence {sortAsc ? '↑' : '↓'}
          </button>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm" role="table" aria-label="Claims table">
          <thead className="text-left text-muted-foreground">
            <tr>
              <th className="px-4 py-2 w-[50%]">Claim</th>
              <th className="px-4 py-2">Verdict</th>
              <th className="px-4 py-2">Confidence</th>
              <th className="px-4 py-2">Evidence</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r: any, idx: number) => (
              <tr key={idx} className="border-t">
                <td className="px-4 py-2 align-top">{r.claim?.text}</td>
                <td className="px-4 py-2 align-top">
                  {r.verdict && (
                    <span className={`inline-flex items-center px-2 py-1 rounded-md border text-xs ${verdictColor(r.verdict.label)}`}>
                      {labelText(r.verdict.label)}
                    </span>
                  )}
                </td>
                <td className="px-4 py-2 align-top">
                  <div className="min-w-[100px]">
                    <div className="h-2 rounded bg-muted">
                      <div className="h-2 rounded bg-primary" style={{ width: `${confidencePercent(r.verdict?.confidence)}%` }} />
                    </div>
                    <div className="text-xs text-muted-foreground mt-1">{confidencePercent(r.verdict?.confidence)}%</div>
                  </div>
                </td>
                <td className="px-4 py-2 align-top">
                  {r.evidence ? (
                    <button
                      className="text-xs px-2 py-1 rounded-md border hover:bg-muted"
                      onClick={() => openEvidence(r.claim.id)}
                    >
                      {r.evidence.source || r.evidence.doc_id}
                    </button>
                  ) : (
                    <span className="text-xs text-muted-foreground">—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function labelText(v: VerdictLabel): string {
  switch (v) {
    case 'supported':
      return 'Supported'
    case 'refuted':
      return 'Refuted'
    default:
      return 'Insufficient'
  }
} 