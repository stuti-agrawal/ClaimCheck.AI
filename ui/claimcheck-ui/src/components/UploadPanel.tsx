import { useState, useCallback, useMemo } from 'react'
import { Upload, Play } from 'lucide-react'
import { useAppStore } from '@/store/appStore'
import { formatBytes } from '@/lib/utils'

export function UploadPanel() {
  const [file, setFile] = useState<File | null>(null)
  const [duration, setDuration] = useState<number | null>(null)
  const startRun = useAppStore((s) => s.startRun)

  const onFiles = useCallback((files: FileList | null) => {
    if (!files || files.length === 0) return
    const f = files[0]
    setFile(f)
    // compute duration
    const url = URL.createObjectURL(f)
    const audio = new Audio(url)
    audio.addEventListener('loadedmetadata', () => {
      setDuration(audio.duration)
      URL.revokeObjectURL(url)
    })
  }, [])

  const handleDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    onFiles(e.dataTransfer.files)
  }, [onFiles])

  const handleBrowse = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    onFiles(e.target.files)
  }, [onFiles])

  const disabled = !file
  const durationText = useMemo(() => {
    if (duration == null) return '—'
    const m = Math.floor(duration / 60)
    const s = Math.round(duration % 60)
    return `${m}:${s.toString().padStart(2, '0')}`
  }, [duration])

  return (
    <div className="space-y-4" aria-label="Upload audio">
      <div
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
        className="border-2 border-dashed rounded-lg p-6 text-center hover:bg-muted/50"
      >
        <div className="flex flex-col items-center gap-2">
          <Upload />
          <p className="text-sm text-muted-foreground">Drag and drop WAV/MP3/M4A here or click to browse</p>
          <input
            type="file"
            accept="audio/wav, audio/mpeg, audio/mp4, audio/x-m4a, audio/aac"
            onChange={handleBrowse}
            className="mt-2"
          />
        </div>
      </div>

      {file && (
        <div className="text-sm bg-secondary text-secondary-foreground rounded-md p-3 flex flex-wrap gap-4">
          <span className="font-medium">{file.name}</span>
          <span>Size: {formatBytes(file.size)}</span>
          <span>Duration: {durationText}</span>
        </div>
      )}

      <div className="flex justify-end">
        <button
          disabled={disabled}
          onClick={() => file && startRun('audio', { file })}
          className={`inline-flex items-center gap-2 px-4 py-2 rounded-md ${disabled ? 'bg-muted text-muted-foreground' : 'bg-primary text-primary-foreground hover:opacity-90'}`}
        >
          <Play size={16} /> Run
        </button>
      </div>
    </div>
  )
} 