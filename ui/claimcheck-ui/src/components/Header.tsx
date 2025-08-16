import { useEffect, useState } from 'react'
import { Moon, Sun } from 'lucide-react'

export function Header() {
  return (
    <header className="border-b bg-background/60 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-lg font-bold">ClaimCheck.AI</span>
          <span className="text-xs px-2 py-1 rounded-full border bg-muted text-muted-foreground">IBM watsonx powered</span>
        </div>
        <ThemeToggle />
      </div>
    </header>
  )
}

function ThemeToggle() {
  const [isDark, setIsDark] = useState(false)

  useEffect(() => {
    const saved = localStorage.getItem('cc_theme')
    const prefers = window.matchMedia('(prefers-color-scheme: dark)').matches
    const dark = saved ? saved === 'dark' : prefers
    setIsDark(dark)
  }, [])

  function toggle() {
    const next = !isDark
    setIsDark(next)
    document.documentElement.classList.toggle('dark', next)
    localStorage.setItem('cc_theme', next ? 'dark' : 'light')
  }

  return (
    <button
      className="inline-flex items-center gap-2 text-sm px-3 py-2 rounded-md border hover:bg-muted"
      aria-label="Toggle color theme"
      onClick={toggle}
    >
      {isDark ? <Sun size={16} /> : <Moon size={16} />}
      <span className="hidden sm:inline">{isDark ? 'Light' : 'Dark'} mode</span>
    </button>
  )
} 