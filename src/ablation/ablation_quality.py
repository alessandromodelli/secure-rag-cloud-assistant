"""
Esecuzione dell'ablation study per misurare la qualità del sistema nelle differenti configurazioni.

Metriche misurate:
- Recall@K: il file target viene recuperato correttamente?
- Precision@K: quanti dei documenti recuperati sono rilevanti?
- False Positive Rate L3 (FPR L3): l'Output Filter redige contenuto non segreto?

Recall e Precision vengono contati su documenti distinti e non su chunk, quindi più
chunk dello stesso documento nei top-k contano come un documento recuperato.

Eseguibile con: python -m src.ablation.ablation_quality
Resume: rilancia lo stesso comando; le coppie (config, query) già salvate vengono saltate.
"""

import csv
import time
from collections import defaultdict
from pathlib import Path
import sys

from src.ablation.ablation_configs import CONFIGS
from src.ablation.rag_ablation import answer
from src.ablation.query_set import QUERY_ROLE, QUALITY_QUERIES

from src.iar.identity import UserIdentity

OUT_PATH = "quality_results.csv"

# Colonne fisse: servono per scrivere l'header PRIMA della prima riga (streaming).
FIELDNAMES = [
    "config",
    "iar",
    "query_firewall",
    "output_filter",
    "query",
    "target",
    "answer",
    "target_retrieved",
    "firewall_blocked",
    "n_context_docs",
    "n_relevant_retrieved",
    "n_relevant_total",
    "precision_at_k",
    "output_redacted",
    "sources_in_context",
    "error",
]

MAX_RETRIES = 2  # tentativi extra sul timeout dell'LLM
RETRY_BACKOFF_S = 3.0  # attesa crescente tra i tentativi


def distinct_docs(sources) -> set[str]:
    """Documenti distinti presenti nel contesto (collassa i chunk per source)."""
    return {s.source for s in sources}


def _is_transient(exc: Exception) -> bool:
    """Timeout/connessione: vale la pena riprovare. Altri errori: falliscono subito."""
    name = exc.__class__.__name__.lower()
    return "timeout" in name or "connect" in name


def _completed_pairs(path: str) -> set[tuple[str, str]]:
    """(config, query) già presenti nel CSV, per il resume."""
    done: set[tuple[str, str]] = set()
    p = Path(path)
    if p.exists():
        with p.open(newline="") as f:
            for r in csv.DictReader(f):
                done.add((r["config"], r["query"]))
    return done


def _answer_with_retry(query_text, identity, conf):
    """Chiama answer() con retry sul timeout. Rilancia se non transitorio o esauriti i tentativi."""
    last = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            return answer(query_text, identity, defense_config=conf)
        except (
            Exception
        ) as exc:  # se timeout LLM ripova fino a MAX_RETRIES e poi va avanti
            last = exc
            if not _is_transient(exc) or attempt == MAX_RETRIES:
                raise
            wait = RETRY_BACKOFF_S * (attempt + 1)
            print(
                f"      timeout LLM (tentativo {attempt + 1}/{MAX_RETRIES}); riprovo tra {wait:.0f}s..."
            )
            time.sleep(wait)
    raise last  # difensivo, non raggiungibile


def _flatten(text: str | None) -> str:
    """Risposta su una sola riga fisica, reversibile: newline -> '\\n' letterale."""
    return (text or "").replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\\n")


def run_quality(out_path: str = OUT_PATH, resume: bool = True) -> None:
    identity = UserIdentity(user_id=f"user_{QUERY_ROLE}", role=QUERY_ROLE)

    done = _completed_pairs(out_path) if resume else set()
    append = bool(done)

    t_start = time.perf_counter()
    completed = 0  # query effettivamente eseguite in questo run (esclusi skip e errori)

    try:
        with open(out_path, "a" if append else "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            if not append:
                writer.writeheader()
                f.flush()

            for conf in CONFIGS.values():
                print(
                    f"---- {conf.label} (QF:{conf.query_firewall} IAR:{conf.iar} OF:{conf.output_filter}) ----"
                )
                for query in QUALITY_QUERIES:
                    if (conf.label, query.query_id) in done:
                        print(f"  [skip, già salvata] {query.query_id}")
                        continue

                    print(f"--- Executing query: {query.query} ---")

                    try:
                        resp = _answer_with_retry(query.query, identity, conf)
                    except Exception as exc:  # noqa: BLE001
                        print(
                            f"  !! ERRORE su '{query.query_id}': {exc.__class__.__name__}: {exc} — riga salvata come errore, continuo."
                        )
                        writer.writerow(
                            {
                                "config": conf.label,
                                "iar": conf.iar,
                                "query_firewall": conf.query_firewall,
                                "output_filter": conf.output_filter,
                                "query": query.query_id,
                                "target": query.target,
                                "answer": "",
                                "target_retrieved": "",
                                "firewall_blocked": "",
                                "n_context_docs": "",
                                "n_relevant_retrieved": "",
                                "n_relevant_total": len(query.relevant_set()),
                                "precision_at_k": "",
                                "output_redacted": "",
                                "sources_in_context": "",
                                "error": f"{exc.__class__.__name__}: {exc}",
                            }
                        )
                        f.flush()
                        continue

                    context_docs = distinct_docs(resp.sources)
                    relevant = query.relevant_set()

                    firewall_blocked = len(resp.sources) == 0 and conf.query_firewall
                    target_retrieved = query.target in context_docs

                    n_context_docs = len(context_docs)
                    n_relevant_retrieved = len(context_docs & relevant)
                    precision = (
                        (n_relevant_retrieved / n_context_docs)
                        if n_context_docs
                        else None
                    )

                    output_redacted = conf.output_filter and "[REDACTED" in (
                        resp.answer or ""
                    )

                    writer.writerow(
                        {
                            "config": conf.label,
                            "iar": conf.iar,
                            "query_firewall": conf.query_firewall,
                            "output_filter": conf.output_filter,
                            "query": query.query_id,
                            "target": query.target,
                            "answer": _flatten(resp.answer),
                            "target_retrieved": target_retrieved,
                            "firewall_blocked": firewall_blocked,
                            "n_context_docs": n_context_docs,
                            "n_relevant_retrieved": n_relevant_retrieved,
                            "n_relevant_total": len(relevant),
                            "precision_at_k": (
                                precision if precision is not None else ""
                            ),
                            "output_redacted": output_redacted,
                            "sources_in_context": "|".join(sorted(context_docs)),
                            "error": "",
                        }
                    )
                    f.flush()
                    completed += 1
    finally:
        elapsed = time.perf_counter() - t_start
        m, s = divmod(int(elapsed), 60)
        h, m = divmod(m, 60)
        avg = f" | mean {elapsed / completed:.1f}s/query" if completed else ""
        print(
            f"\nExecution time: {h:02d}:{m:02d}:{s:02d} ({elapsed:.1f}s) — {completed} queries executed {avg}"
        )

    # Aggregazione finale letta dal file: riflette esattamente ciò che è stato salvato.
    show_quality_by_configuration(out_path)


def _aggregate(rows: list[dict]) -> None:
    """Recall@K, Precision@K e FPR_L3 per config. Le righe con 'error' sono escluse da tutti i denominatori."""
    recall_hit = defaultdict(int)
    recall_tot = defaultdict(int)
    prec_sum = defaultdict(float)
    prec_n = defaultdict(int)
    l3_fp = defaultdict(int)
    l3_tot = defaultdict(int)  # denom: query con OF attivo
    errored = defaultdict(int)

    for r in rows:
        c = r["config"]

        # Normalizza i booleani: dal dict Python arrivano bool, dal CSV arrivano stringhe.
        def truthy(v) -> bool:
            return v is True or str(v).strip().lower() == "true"

        if str(r.get("error", "")).strip():  # query fallita: esclusa da ogni metrica
            errored[c] += 1
            continue

        # Recall: conta solo le query NON bloccate dal firewall. Una query bloccata
        # non è un fallimento di recall, è un falso positivo di L1.
        if not truthy(r["firewall_blocked"]):
            recall_tot[c] += 1
            recall_hit[c] += int(truthy(r["target_retrieved"]))

        # Precision: solo dove è definita (contesto non vuoto).
        p = r.get("precision_at_k", "")
        if p not in ("", None):
            prec_sum[c] += float(p)
            prec_n[c] += 1

        # FPR L3: frazione di query legittime la cui risposta è stata redatta.
        if truthy(r["output_filter"]):
            l3_tot[c] += 1
            l3_fp[c] += int(truthy(r["output_redacted"]))

    print("\n=== Qualità e costo per configurazione ===")
    for c in sorted(recall_tot | prec_n, key=lambda x: int(x[1:])):
        rec = recall_hit[c] / recall_tot[c] if recall_tot[c] else float("nan")
        prec = prec_sum[c] / prec_n[c] if prec_n[c] else float("nan")
        l3 = f"{l3_fp[c]}/{l3_tot[c]}" if l3_tot[c] else "  -  "
        extra = f"   [{errored[c]} query in errore, escluse]" if errored[c] else ""
        print(f"  {c}: Recall@K={rec:.3f}  Precision@K={prec:.3f}  FPR_L3={l3}{extra}")


def load_quality_results(path: str | Path) -> list[dict[str, str]]:
    """Carica le righe dal CSV dei risultati."""
    with Path(path).open(newline="") as f:
        return list(csv.DictReader(f))


def show_quality_by_configuration(path: str | Path) -> None:
    """Calcola e stampa le metriche di utilità per ogni configurazione dal CSV salvato."""
    rows = load_quality_results(path)
    if not rows:
        print("\nNessun risultato disponibile.")
        return
    _aggregate(rows)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] != "--load-results":
            print("Use: python -m src.ablation.ablation_quality --load-results")
        else:
            show_quality_by_configuration(OUT_PATH)
    else:
        run_quality()
