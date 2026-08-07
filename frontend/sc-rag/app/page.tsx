"use client";

import { FormEvent, useState } from "react";

type Source = Record<string, unknown>;

type QueryResponse = {
  query: string;
  identity?: { user_id?: string; role?: string };
  answer: string;
  sources?: Source[];
  audit_log?: Record<string, unknown> | string[];
  stats?: Record<string, unknown>;
};

function sourceText(source: Source) {
  return String(source.title ?? source.file_name ?? source.filename ?? source.document ?? source.source ?? "Untitled document");
}

export default function Home() {
  const [query, setQuery] = useState("");
  const [role, setRole] = useState("developer");
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const cleanQuery = query.trim();
    if (!cleanQuery) return;

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "";
      const response = await fetch(`${baseUrl}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: cleanQuery, user_role: role })
      });
      console.log(response)

      if (!response.ok) {
        const detail = await response.json().catch(() => null);
        throw new Error(detail?.detail || "Unable to process the request.");
      }
      setResult(await response.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : "An unexpected error occurred.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="relative min-h-screen overflow-hidden bg-[var(--page-background)]">
      <div aria-hidden="true" className="pointer-events-none absolute -left-32 top-20 h-80 w-80 rounded-full bg-amber-200/35 blur-3xl" />
      <div aria-hidden="true" className="pointer-events-none absolute -right-24 top-80 h-96 w-96 rounded-full bg-orange-100/80 blur-3xl" />
      <header className="relative border-b border-white/70 bg-white/70 backdrop-blur-xl">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="grid h-10 place-items-center rounded-2xl px-2 bg-[var(--brand)] text-lg font-black text-slate-900 shadow-lg shadow-amber-300/50">SCRAG</div>
            <div>
              <h1 className="text-base font-semibold tracking-tight text-slate-900">AI</h1>
              <p className="text-xs text-slate-500">Secure Cloud Retrieval Augmented Generation</p>
            </div>
          </div>
        </div>
      </header>

      <div className="relative mx-auto max-w-5xl px-6 py-16 sm:py-20">
        <section className="mx-auto max-w-3xl text-center">
          <h2 className="text-4xl font-black tracking-[-0.045em] text-slate-950 sm:text-5xl">Ask your <span className="text-amber-600">documents.</span></h2>
          <p className="mx-auto mt-5 max-w-2xl text-base leading-7 text-slate-600">Contextual answers from the content your role is authorized to access.</p>
        </section>

        <form onSubmit={handleSubmit} className="mx-auto mt-10 max-w-3xl rounded-3xl border border-white/80 bg-white/85 p-3 shadow-xl shadow-slate-300/30 backdrop-blur-sm sm:p-4">
          <textarea
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Show me the configuration of the payment-service."
            rows={4}
            className="w-full resize-none rounded-2xl border-0 bg-slate-100/75 p-4 text-base text-slate-900 outline-none placeholder:text-slate-400 transition focus:bg-white focus:ring-2 focus:ring-[var(--brand)]"
          />
          <div className="mt-3 flex flex-col gap-3 border-t border-slate-100 pt-3 sm:flex-row sm:items-center sm:justify-between">
            <label className="flex items-center gap-2 text-sm text-slate-600">
              <span>Role</span>
              <input list="roles" value={role} onChange={(event) => setRole(event.target.value)} className="w-32 rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-sm font-medium text-slate-700 outline-none focus:border-[var(--brand)]" />
              <datalist id="roles"><option value="public" /></datalist>
            </label>
            <button type="submit" disabled={loading} className="rounded-xl bg-[var(--brand)] px-5 py-2.5 text-sm font-bold text-slate-900 shadow-md shadow-amber-300/40 transition duration-200 hover:-translate-y-0.5 hover:bg-[var(--brand-dark)] hover:shadow-lg disabled:cursor-not-allowed disabled:bg-slate-300 disabled:hover:translate-y-0">
              {loading ? "Searching…" : "Ask AI"}
            </button>
          </div>
        </form>

        {error && <p role="alert" className="mx-auto mt-6 max-w-3xl rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p>}

        {result && (
          <section className="mx-auto mt-8 max-w-3xl space-y-4">
            <article className="rounded-3xl border border-white/80 bg-white/85 p-6 shadow-xl shadow-slate-300/30 backdrop-blur-sm">
              <div className="mb-4 flex items-center justify-between gap-4">
                <h3 className="font-semibold text-slate-900">Answer</h3>
                {result.identity?.role && <span className="rounded-full bg-amber-50 px-2.5 py-1 text-xs font-medium text-amber-800">{result.identity.role}</span>}
              </div>
              <p className="whitespace-pre-wrap leading-7 text-slate-700">{result.answer}</p>
            </article>

            {(result.sources?.length ?? 0) > 0 && (
              <article className="rounded-3xl border border-white/80 bg-white/85 p-6 shadow-xl shadow-slate-300/30 backdrop-blur-sm">
                <h3 className="mb-3 font-semibold text-slate-900">Sources</h3>
                <ul className="space-y-2">
                  {result.sources?.map((source, index) => <li key={index} className="rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-700">{sourceText(source)}</li>)}
                </ul>
              </article>
            )}

            {result.audit_log && (
              <details className="rounded-2xl border border-white/80 bg-white/85 px-5 py-4 text-sm text-slate-600 shadow-sm backdrop-blur-sm">
                <summary className="cursor-pointer font-medium text-slate-800">Audit details</summary>
                <pre className="mt-3 overflow-x-auto whitespace-pre-wrap rounded-lg bg-slate-950 p-4 text-xs leading-5 text-slate-100">{JSON.stringify(result.audit_log, null, 2)}</pre>
              </details>
            )}
          </section>
        )}
      </div>
    </main>
  );
}
