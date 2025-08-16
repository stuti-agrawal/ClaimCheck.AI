import axios from 'axios'
import type { CallReport } from '@/lib/types'

const baseURL = import.meta.env.VITE_API_BASE ?? 'http://127.0.0.1:8000'

export const api = axios.create({
  baseURL,
  timeout: 120000,
})

export type Health = {
  ok: boolean
  watsonx: boolean
  stt: boolean
  models?: Record<string, any>
}

export async function health(): Promise<Health> {
  const { data } = await api.get('/health/ibm')
  return data
}

export async function rebuildKb(): Promise<{ ok: boolean }> {
  const { data } = await api.post('/kb/rebuild')
  return data
}

export async function processAudio(file: File): Promise<CallReport> {
  const form = new FormData()
  form.append('file', file)
  const { data } = await api.post('/process-audio', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function processTranscript(text: string): Promise<CallReport> {
  const { data } = await api.post('/process-transcript', { text })
  return data
} 