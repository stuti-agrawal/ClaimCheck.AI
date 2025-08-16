# ClaimCheck.AI UI

A React + Vite + TypeScript single-page app with TailwindCSS and minimal shadcn-style design.

## Prerequisites
- Node.js 18+
- pnpm (preferred) or npm/yarn

## Setup
```bash
pnpm install
```

## Run Dev Server
```bash
pnpm dev
```
- App: `http://localhost:5173`
- Backend base URL is read from `VITE_API_BASE` (default `http://127.0.0.1:8000`).
  - Create `.env` and set `VITE_API_BASE=http://127.0.0.1:8000` if needed.

## Build
```bash
pnpm build
pnpm preview
```

## Features
- Upload audio or paste transcript and run
- Pipeline stepper with optimistic progression
- Results summary with copy/download/print
- Claims table with verdict filters and evidence drawer
- Transcript viewer (collapsible)
- Run history (localStorage) and sample data

## Accessibility
- Keyboard navigable
- AA contrast
- Roles/aria on tabs, tables, dialogs 