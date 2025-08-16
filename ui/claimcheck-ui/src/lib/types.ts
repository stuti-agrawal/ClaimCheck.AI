export type Claim = {
  id: string
  text: string
  speaker?: string | null
  start?: number
  end?: number
  confidence?: number
}

export type Evidence = {
  doc_id: string
  source?: string
  snippet: string
  score?: number
  metadata?: Record<string, any>
}

export type VerdictLabel = 'supported' | 'refuted' | 'insufficient'

export type Verdict = {
  claim_id: string
  label: VerdictLabel
  confidence?: number
  best_evidence_id?: string
  rationale?: string
  citation_ids?: string[]
}

export type CallReport = {
  call_summary: string
  action_items: string[]
  claim_table: { claim: string; status: string; evidence_source?: string }[]
  claims: Claim[]
  evidence: Evidence[]
  verdicts: Verdict[]
  evidence_by_claim?: Record<string, Evidence[]>
}

export type InputKind = 'audio' | 'transcript' | 'sample'

export type RunRecord = {
  id: string
  startedAt: number
  inputKind: InputKind
  report?: CallReport
  error?: string
} 