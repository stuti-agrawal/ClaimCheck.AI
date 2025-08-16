import { useEffect, useState } from 'react'
import { health, rebuildKb, type Health } from '@/lib/api'

export function SettingsPanel() {
  const [data, setData] = useState<Health | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    health().then(setData).catch((e) => setError(e?.message || 'Failed to load health'))
  }, [])

  return (
    <div className="space-y-4" aria-label="Settings">
      <div>
        <h3 className="font-medium">Models</h3>
        {!data && !error && <p className="text-sm text-muted-foreground">Loading...</p>}
        {error && <p className="text-sm text-red-600">{error}</p>}
        {data && (
          <div className="text-sm bg-secondary rounded-md p-3 overflow-auto">
            <div>Status: {data.ok ? 'OK' : 'Degraded'}</div>
            <div>watsonx: {data.watsonx ? 'Yes' : 'No'}</div>
            <div>stt: {data.stt ? 'Yes' : 'No'}</div>
            {data.models && (
              <pre className="mt-2 text-xs whitespace-pre-wrap">{JSON.stringify(data.models, null, 2)}</pre>
            )}
          </div>
        )}
      </div>
      <div>
        <h3 className="font-medium">Knowledge Base</h3>
        <button
          onClick={async () => { try { await rebuildKb(); alert('KB rebuild requested'); } catch (e) { alert('Failed to rebuild KB'); } }}
          className="inline-flex items-center gap-2 px-3 py-2 rounded-md border hover:bg-muted"
        >
          Rebuild Index
        </button>
      </div>
    </div>
  )
} 