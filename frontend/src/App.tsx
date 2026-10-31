export default function App() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-slate-50 p-6 text-slate-900">
      <main className="w-full max-w-md rounded-xl border border-slate-200 bg-white p-8 text-center shadow-sm">
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-indigo-50 text-xl font-bold text-indigo-600">
          AG
        </div>
        <h1 className="mb-2 text-2xl font-semibold tracking-tight text-slate-900">
          AccessGuard AI
        </h1>
        <p className="mb-6 text-sm text-slate-500">
          Accessibility observability, automated auditing, and human-approved remediation.
        </p>
        <div className="inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-xs font-medium text-emerald-700">
          <span className="h-2 w-2 rounded-full bg-emerald-500"></span>
          Toolchain Initialized
        </div>
      </main>
    </div>
  )
}
