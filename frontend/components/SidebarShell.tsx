import Link from 'next/link'
import { useRouter } from 'next/router'
import type { ReactNode } from 'react'
import { useMemo, useState } from 'react'

type NavItem = {
  label: string
  href: string
  description?: string
}

type SidebarShellProps = {
  title: string
  subtitle?: string
  children: ReactNode
  navItems?: NavItem[]
}

const DEFAULT_NAV: NavItem[] = [
  { label: 'RAG Tool', href: '/', description: 'Upload + ask questions' },
  { label: 'Documents', href: '/documents', description: 'Manage indexed docs' },
  { label: 'AI Codebase Assistant', href: '/assistant', description: 'Architecture & Code Gen' },
]

function cx(...parts: Array<string | false | null | undefined>) {
  return parts.filter(Boolean).join(' ')
}

export function SidebarShell({ title, subtitle, children, navItems }: SidebarShellProps) {
  const router = useRouter()
  const [open, setOpen] = useState(false)

  const items = navItems ?? DEFAULT_NAV
  const activePath = router.pathname

  const activeLabel = useMemo(() => {
    const hit = items.find((i) => i.href === activePath)
    return hit?.label ?? 'Tools'
  }, [activePath, items])

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      {/* Mobile top bar */}
      <div className="sticky top-0 z-20 border-b border-slate-900 bg-slate-950/80 backdrop-blur md:hidden">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <button
            onClick={() => setOpen((v) => !v)}
            className="rounded-lg border border-slate-800 bg-slate-900 px-3 py-2 text-sm text-slate-200 hover:bg-slate-800"
          >
            Menu
          </button>
          <div className="text-sm font-semibold">{activeLabel}</div>
          <div className="w-[64px]" />
        </div>
      </div>

      <div className="mx-auto grid max-w-6xl grid-cols-1 gap-6 px-4 py-8 md:grid-cols-[260px_1fr] md:gap-8 md:py-10">
        {/* Sidebar */}
        <aside
          className={cx(
            'md:block',
            open ? 'block' : 'hidden',
            'rounded-2xl border border-slate-800 bg-slate-900/60 p-4 md:sticky md:top-10 md:h-[calc(100vh-5rem)] md:overflow-auto'
          )}
        >
          <div className="flex items-start justify-between gap-3 md:block">
            <div>
              <div className="text-sm font-semibold text-slate-100">Toolbox</div>
              <div className="mt-1 text-xs text-slate-400">Add more tools over time</div>
            </div>
            <button
              onClick={() => setOpen(false)}
              className="rounded-lg border border-slate-800 bg-slate-950/40 px-2 py-1 text-xs text-slate-200 hover:bg-slate-800 md:hidden"
            >
              Close
            </button>
          </div>

          <div className="mt-4">
            <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Navigation</div>
            <nav className="mt-2 space-y-2">
              {items.map((item) => {
                const isActive = item.href === activePath
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setOpen(false)}
                    className={cx(
                      'block rounded-xl border px-3 py-2',
                      isActive
                        ? 'border-indigo-500/40 bg-indigo-500/10 text-slate-50'
                        : 'border-slate-800 bg-slate-950/40 text-slate-200 hover:bg-slate-800/40'
                    )}
                  >
                    <div className="text-sm font-semibold">{item.label}</div>
                    {item.description ? <div className="mt-0.5 text-xs text-slate-400">{item.description}</div> : null}
                  </Link>
                )
              })}
            </nav>
          </div>

          <div className="mt-6 border-t border-slate-800 pt-4 text-xs text-slate-400">
            Local RAG demo • FastAPI + Next.js + Ollama
          </div>
        </aside>

        {/* Main */}
        <main>
          <header className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
            <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
            {subtitle ? <p className="mt-1 text-sm text-slate-300">{subtitle}</p> : null}
          </header>
          <section className="mt-6">{children}</section>
        </main>
      </div>
    </div>
  )
}


