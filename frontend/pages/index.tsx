import { useEffect, useMemo, useState } from 'react'
import { SidebarShell } from '@/components/SidebarShell'
import type { DocumentsResponse, QueryHit, QueryResponse, UploadResponse } from '@/types/api'

type ApiError = { detail?: string }

async function safeJson<T>(res: Response): Promise<T | ApiError> {
  return (await res.json().catch(() => ({}))) as T | ApiError
}

export default function Home() {
  const [file, setFile] = useState<File | null>(null)
  const [status, setStatus] = useState('')
  const [query, setQuery] = useState('')
  const [topK, setTopK] = useState<number>(3)
  const [answer, setAnswer] = useState('')
  const [docs, setDocs] = useState<DocumentsResponse>({})
  const [sources, setSources] = useState<string[]>([])
  const [hits, setHits] = useState<QueryHit[]>([])
  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  const docCount = useMemo(() => Object.keys(docs || {}).length, [docs])

  async function fetchDocs() {
    try {
      const res = await fetch(`${API_BASE}/documents`)
      const j = (await res.json()) as DocumentsResponse
      setDocs(j || {})
    } catch (e) {
      console.error('failed to fetch docs', e)
    }
  }

  async function upload() {
    if (!file) return
    const fd = new FormData()
    fd.append('file', file)
    setStatus('Uploading…')
    setAnswer('')
    setSources([])
    setHits([])

    try {
      const res = await fetch(`${API_BASE}/upload`, { method: 'POST', body: fd })
      const j = await safeJson<UploadResponse>(res)
      if (!res.ok) throw new Error((j as ApiError)?.detail || `Upload failed (HTTP ${res.status})`)
      const ok = j as UploadResponse
      setStatus(`Uploaded ${file.name} • ${ok.chunks} chunks`)
      await fetchDocs()
    } catch (e) {
      setStatus(`Upload error: ${(e as Error)?.message || String(e)}`)
    }
  }

  async function ask() {
    if (!query.trim()) return
    setAnswer('Thinking…')
    setSources([])
    setHits([])

    try {
      const res = await fetch(`${API_BASE}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, top_k: topK }),
      })
      const j = (await safeJson<QueryResponse>(res)) as QueryResponse | ApiError
      if (!res.ok) throw new Error((j as ApiError)?.detail || 'Query failed')
      const ok = j as QueryResponse
      setAnswer(ok.answer || '')
      setSources(ok.sources || [])
      setHits(ok.hits || [])
    } catch (e) {
      setAnswer(`Error: ${(e as Error)?.message || String(e)}`)
    }
  }

  useEffect(() => {
    fetchDocs()
  }, [])

  return (
    <SidebarShell
      title="Document Q&A (Local RAG)"
      subtitle="Upload PDFs/DOCX/TXT, then ask questions grounded strictly in your documents."
    >
      <div className="grid gap-6 lg:grid-cols-5">
        <section className="lg:col-span-2">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold text-slate-200">Upload</h2>
              <span className="text-xs text-slate-400">{docCount} docs</span>
            </div>

            <div className="mt-3">
              <label className="block cursor-pointer rounded-xl border border-dashed border-slate-700 bg-slate-950/40 px-4 py-6 text-center hover:border-slate-600">
                <input
                  type="file"
                  className="hidden"
                  accept=".pdf,.docx,.txt"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                />
                <div className="text-sm text-slate-200">
                  {file ? (
                    <>
                      <span className="font-medium">{file.name}</span>
                      <span className="ml-2 text-xs text-slate-400">
                        {(file.size / (1024 * 1024)).toFixed(2)} MB
                      </span>
                    </>
                  ) : (
                    'Click to choose a PDF/DOCX/TXT'
                  )}
                </div>
                <div className="mt-1 text-xs text-slate-400">We’ll chunk and index it locally.</div>
              </label>

              <button
                onClick={upload}
                disabled={!file}
                className="mt-3 w-full rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Upload & Index
              </button>

              {status ? (
                <div className="mt-3 rounded-xl border border-slate-800 bg-slate-950/40 px-3 py-2 text-xs text-slate-300">
                  {status}
                </div>
              ) : null}
            </div>
          </div>

          <div className="mt-6 rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
            <h2 className="text-sm font-semibold text-slate-200">Documents</h2>
            <div className="mt-3 space-y-3">
              {Object.keys(docs).length === 0 ? (
                <div className="text-sm text-slate-400">No documents uploaded yet.</div>
              ) : (
                Object.entries(docs).map(([id, meta]) => (
                  <div key={id} className="rounded-xl border border-slate-800 bg-slate-950/40 p-3">
                    <div className="text-sm font-medium text-slate-100">{meta.filename}</div>
                    <div className="mt-1 text-xs text-slate-400">
                      {meta.chunks} chunks • <span className="font-mono">{id}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </section>

        <section className="lg:col-span-3">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <h2 className="text-sm font-semibold text-slate-200">Ask a question</h2>
                <p className="mt-1 text-xs text-slate-400">
                  Tip: ask specific questions; the system will refuse if the info isn’t in your docs.
                </p>
              </div>
              <label className="text-xs text-slate-400">
                Top‑k
                <select
                  value={topK}
                  onChange={(e) => setTopK(Number(e.target.value))}
                  className="ml-2 rounded-lg border border-slate-700 bg-slate-950/40 px-2 py-1 text-slate-200"
                >
                  {[1, 2, 3, 4, 5].map((k) => (
                    <option key={k} value={k}>
                      {k}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <div className="mt-3 flex gap-2">
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="e.g., What are the refund terms in the policy?"
                className="w-full rounded-xl border border-slate-700 bg-slate-950/40 px-4 py-3 text-sm text-slate-100 placeholder:text-slate-500 focus:border-indigo-500 focus:outline-none"
              />
              <button
                onClick={ask}
                className="rounded-xl bg-emerald-600 px-4 py-3 text-sm font-semibold text-white hover:bg-emerald-500"
              >
                Ask
              </button>
            </div>
          </div>

          <div className="mt-6 rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
            <h2 className="text-sm font-semibold text-slate-200">Answer</h2>
            <div className="mt-3 whitespace-pre-wrap rounded-xl border border-slate-800 bg-slate-950/40 p-4 text-sm text-slate-100">
              {answer ? answer : <span className="text-slate-400">Ask a question to see an answer here.</span>}
            </div>

            <div className="mt-5 grid gap-4 md:grid-cols-2">
              <div>
                <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-400">Sources</h3>
                <div className="mt-2 space-y-2">
                  {sources.length === 0 ? (
                    <div className="text-sm text-slate-400">No sources returned.</div>
                  ) : (
                    sources.map((s, i) => (
                      <div key={`${s}-${i}`} className="rounded-xl border border-slate-800 bg-slate-950/40 p-3">
                        <div className="text-sm text-slate-100">{docs[s] ? docs[s].filename : s}</div>
                        <div className="mt-1 text-xs text-slate-400">{docs[s] ? `${docs[s].chunks} chunks` : 'unknown'}</div>
                      </div>
                    ))
                  )}
                </div>
              </div>

              <div>
                <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-400">Top hits</h3>
                <div className="mt-2 space-y-2">
                  {hits.length === 0 ? (
                    <div className="text-sm text-slate-400">No retrieval hits yet.</div>
                  ) : (
                    hits.map((h) => (
                      <div key={h.id} className="rounded-xl border border-slate-800 bg-slate-950/40 p-3">
                        <div className="flex items-center justify-between gap-2">
                          <div className="text-sm font-medium text-slate-100">{h.filename || h.doc_id || 'Document'}</div>
                          {typeof h.score === 'number' ? (
                            <div className="text-xs text-slate-400">score: {h.score.toFixed(3)}</div>
                          ) : null}
                        </div>
                        <div className="mt-1 text-xs text-slate-400">{h.chunk_index != null ? `chunk ${h.chunk_index}` : null}</div>
                        <div className="mt-2 line-clamp-5 text-sm text-slate-200">{h.text}</div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>
    </SidebarShell>
  )
}


