import { useMemo } from 'react'
import { useAppStore } from '@/store/appStore'
import { copyToClipboard, downloadJSON } from '@/lib/utils'
import { Copy, Download, Printer } from 'lucide-react'

export function ResultsSummary() {
  const run = useAppStore((s) => s.runs.find((r) => r.id === s.currentRunId))
  const report = run?.report

  const summary = useMemo(() => report?.call_summary ?? '', [report])

  if (!report) return null

  function onCopy() {
    copyToClipboard(summary)
  }

  function onDownload() {
    downloadJSON(report)
  }

  function onPrint() {
    window.print()
  }

  return (
    <div className="bg-card text-card-foreground rounded-lg border p-4">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold">Executive Summary</h3>
        <div className="flex items-center gap-2">
          <button className="inline-flex items-center gap-1 text-sm px-2 py-1 rounded-md border hover:bg-muted" onClick={onCopy}>
            <Copy size={14} /> Copy
          </button>
          <button className="inline-flex items-center gap-1 text-sm px-2 py-1 rounded-md border hover:bg-muted" onClick={onDownload}>
            <Download size={14} /> Download JSON
          </button>
          <button className="inline-flex items-center gap-1 text-sm px-2 py-1 rounded-md border hover:bg-muted" onClick={onPrint}>
            <Printer size={14} /> Download PDF
          </button>
        </div>
      </div>
      <p className="mt-3 text-sm leading-6 whitespace-pre-line">{summary}</p>
      {report.action_items?.length > 0 && (
        <div className="mt-4">
          <h4 className="font-medium">Action Items</h4>
          <ul className="list-disc list-inside text-sm mt-2 space-y-1">
            {report.action_items.map((a, idx) => (
              <li key={idx}>{a}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
} 