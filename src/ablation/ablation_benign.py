"""
Esecuzione dell'ablation study su query benigne per misurare la qualità del sistema nelle differenti configurazioni.

Metriche misurate:
- Recall@K: il file target viene recuperato correttamente?
- Precision@K: quanti dei documenti recuperati sono rilevanti?
- False Positive Rate L1 (FPR L1): il Query Firewall blocca query legittime?
- False Positive Rate L3 (FPR L2): l'Output Filter redige contenuto non segreto?

Recall e Precision vengono contati su documenti distinti e non su chunk, quindi più
chunk dello stesso documento nei top-k contano come un documento
recuperato.

Eseguibile con: python -m src.ablation.ablation_benign
"""

import csv
from collections import defaultdict

from src import config
from src.ablation.ablation_configs import CONFIGS
from src.RAG.rag_ablation import answer
from src.ablation.query_set import QUERY_ROLE, BENIGN_QUERIES

from src.IAR.identity import UserIdentity


def distinct_docs(sources) -> set[str]:
    """Documenti distinti presenti nel contesto (collassa i chunk per source)."""
    return {s.source for s in sources}


def run_benign(out_path: str = "benign_results.csv") -> None:
    identity = UserIdentity(user_id=f"user_{QUERY_ROLE}", role=QUERY_ROLE)
    rows: list[dict] = []

    for conf in CONFIGS.values():
        print(
            f"---- {conf.label} (QF:{conf.query_firewall} IAR:{conf.iar} OF:{conf.output_filter}) ----"
        )
        for query in BENIGN_QUERIES:
            print(f"--- Executing query: {query.query} ---")
            resp = answer(query.query, identity, defense_config=conf)

            context_docs = distinct_docs(resp.sources)
            relevant = query.relevant_set()

            # FPR L1: Se il firewall blocca la query, il retrieval non fallisce
            firewall_blocked = len(resp.sources) == 0 and conf.query_firewall

            # Recall@K, verifica se target presente nel contesto
            target_retrieved = query.target in context_docs

            # Precision@K a livello documento = documenti pertinenti / documenti distinti recuperati.
            # Denominatore = documenti nel contesto, non k,
            # perché con IAR il contesto può contenere meno di k documenti distinti.
            n_context_docs = len(context_docs)
            n_relevant_retrieved = len(context_docs & relevant)
            precision = (
                (n_relevant_retrieved / n_context_docs) if n_context_docs else None
            )

            # Recall@K standard
            # n_relevant_total = len(relevant)
            # standard_recall = (
            #     (n_relevant_retrieved / n_relevant_total) if n_relevant_total else 0.0,
            # )

            # FPR L3: Verifica se l'output filter ha redatto qualcosa su una query benigna.
            output_redacted = conf.output_filter and "[REDACTED" in (resp.answer or "")

            rows.append(
                {
                    "config": conf.label,
                    "iar": conf.iar,
                    "query_firewall": conf.query_firewall,
                    "output_filter": conf.output_filter,
                    "query": query.query_id,
                    "borderline": query.borderline,
                    "target": query.target,
                    # utilità
                    "target_retrieved": target_retrieved,
                    "firewall_blocked": firewall_blocked,
                    # qualità del retriever
                    "n_context_docs": n_context_docs,
                    "n_relevant_retrieved": n_relevant_retrieved,
                    "n_relevant_total": len(relevant),
                    "precision_at_k": precision,
                    # costo delle difese (falsi positivi su traffico legittimo)
                    "output_redacted": output_redacted,
                    "sources_in_context": "|".join(sorted(context_docs)),
                }
            )

    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    _report(rows)


def _report(rows: list[dict]) -> None:
    # Recall@K e Precision@K per config; FPR L1/L3 per config.
    recall_hit = defaultdict(int)
    recall_tot = defaultdict(int)
    prec_sum = defaultdict(float)
    prec_n = defaultdict(int)
    l1_fp = defaultdict(int)
    l1_tot = defaultdict(int)  # denom: query con QF attivo
    l3_fp = defaultdict(int)
    l3_tot = defaultdict(int)  # denom: query con OF attivo

    for r in rows:
        c = r["config"]

        # Recall: conta solo le query NON bloccate dal firewall. Una query
        # bloccata non è un fallimento di recall, è un falso positivo di L1
        if not r["firewall_blocked"]:
            recall_tot[c] += 1
            recall_hit[c] += int(r["target_retrieved"])

        if r["precision_at_k"] is not None:
            prec_sum[c] += float(r["precision_at_k"])
            prec_n[c] += 1

        # FPR L1: frazione di query legittime bloccate dal firewall.
        if r["query_firewall"] == "True" or r["query_firewall"] is True:
            l1_tot[c] += 1
            l1_fp[c] += int(bool(r["firewall_blocked"]))

        # FPR L3: frazione di query legittime la cui risposta è stata redatta.
        if r["output_filter"] == "True" or r["output_filter"] is True:
            l3_tot[c] += 1
            l3_fp[c] += int(bool(r["output_redacted"]))

    print("\n=== Qualità e costo per configurazione ===")
    for c in sorted(recall_tot | prec_n, key=lambda x: int(x[1:])):
        rec = recall_hit[c] / recall_tot[c] if recall_tot[c] else float("nan")
        prec = prec_sum[c] / prec_n[c] if prec_n[c] else float("nan")
        l1 = f"{l1_fp[c]}/{l1_tot[c]}" if l1_tot[c] else "  -  "
        l3 = f"{l3_fp[c]}/{l3_tot[c]}" if l3_tot[c] else "  -  "
        print(
            f"  {c}: Recall@K={rec:.3f}  Precision@K={prec:.3f}  "
            f"FPR_L1={l1}  FPR_L3={l3}"
        )


if __name__ == "__main__":
    run_benign()
