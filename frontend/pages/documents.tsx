import { useEffect, useMemo, useState } from 'react'
import { SidebarShell } from '@/components/SidebarShell'
import type { DocumentsResponse } from '@/types/api'

export default function DocumentsPage() {
  const [docs, setDocs] = useState<DocumentsResponse>({})
  const [loading, setLoading] = useState(true)
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  const docEntries = useMemo(() => Object.entries(docs || {}), [docs])

  async function fetchDocs() {
    setLoading(true)
    try {
      const res = await fetch(`${API_BASE}/documents`)
      const j = (await res.json()) as DocumentsResponse
      setDocs(j || {})
    } catch (e) {
      console.error('failed to fetch docs', e)
      setDocs({})
    } finally {
      setLoading(false)
    }
  }

  async function deleteDoc(id: string) {
    const ok = window.confirm('Delete this document and its indexed chunks?')
    if (!ok) return
    setDeletingId(id)
    try {
      const res = await fetch(`${API_BASE}/documents/${id}`, { method: 'DELETE' })
      const j = (await res.json().catch(() => ({}))) as { detail?: string }
      if (!res.ok) throw new Error(j?.detail || 'Delete failed')
      await fetchDocs()
    } catch (e) {
      alert((e as Error)?.message || String(e))
    } finally {
      setDeletingId(null)
    }
  }

  useEffect(() => {
    fetchDocs()
  }, [])

  return (
    <SidebarShell title="Uploaded Documents" subtitle="Manage and inspect what’s currently indexed.">
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
        {loading ? (
          <div className="text-sm text-slate-300">Loading…</div>
        ) : docEntries.length === 0 ? (
          <div className="text-sm text-slate-400">No documents uploaded.</div>
        ) : (
          <div className="grid gap-3 md:grid-cols-2">
            {docEntries.map(([id, meta]) => (
              <div key={id} className="rounded-xl border border-slate-800 bg-slate-950/40 p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="text-sm font-semibold text-slate-100">{meta.filename}</div>
                  <button
                    onClick={() => deleteDoc(id)}
                    disabled={deletingId === id}
                    className="rounded-lg border border-slate-800 bg-slate-900 px-3 py-1.5 text-xs text-slate-200 hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
                    title="Delete document"
                  >
                    {deletingId === id ? 'Deleting…' : 'Delete'}
                  </button>
                </div>
                <div className="mt-2 flex flex-wrap gap-2 text-xs text-slate-400">
                  <span className="rounded-md border border-slate-800 bg-slate-900 px-2 py-1">{meta.chunks} chunks</span>
                  <span className="rounded-md border border-slate-800 bg-slate-900 px-2 py-1 font-mono">{id}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </SidebarShell>
  )
}


