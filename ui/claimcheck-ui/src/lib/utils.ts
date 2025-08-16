import type { CallReport, VerdictLabel } from '@/lib/types'

export function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`
}

export function verdictColor(label: VerdictLabel): string {
  switch (label) {
    case 'supported':
      return 'bg-supported/15 text-supported border-supported/30'
    case 'refuted':
      return 'bg-refuted/15 text-refuted border-refuted/30'
    default:
      return 'bg-insufficient/15 text-insufficient border-insufficient/30'
  }
}

export function confidencePercent(v?: number): number {
  if (!v && v !== 0) return 0
  const pct = Math.max(0, Math.min(1, v)) * 100
  return Math.round(pct)
}

export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch {
    return false
  }
}

export function downloadJSON(report: CallReport, filename = 'call_report.json') {
  const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

export function wordCount(text: string): number {
  return (text.trim().match(/\S+/g) || []).length
} 