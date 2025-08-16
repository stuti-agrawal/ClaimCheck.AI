import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

function useSystemPrefersDark(): boolean {
  if (typeof window === 'undefined') return false
  return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
}

function initTheme() {
  const saved = localStorage.getItem('cc_theme')
  const root = document.documentElement
  const prefersDark = useSystemPrefersDark()
  const isDark = saved ? saved === 'dark' : prefersDark
  root.classList.toggle('dark', isDark)
}

initTheme()

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
) 