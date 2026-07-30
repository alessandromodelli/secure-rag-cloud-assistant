"""
Esecuzione dell'ablation study sull'asse Privilege Escalation

Metrica relativa da misurare: URR

Eseguibile con: python -m src.ablation.ablation_urr

"""

import csv
from src.iar.identity import authorize_chunk, UserIdentity
from src.ablation.rag_ablation import answer
from src.ablation.ablation_configs import CONFIGS
from src.ablation.query_set import PRIVILEGE_QUERIES, QUERY_ROLE


def run_urr(out_path: str = "urr_results.csv") -> None:
    identity = UserIdentity(user_id="attacker", role=QUERY_ROLE)
    rows: list[dict] = []

    for conf in CONFIGS.values():
        print(
            f"---- {conf.label} (QF:{conf.query_firewall} IAR:{conf.iar} OF:{conf.output_filter}) ----"
        )
        for q in PRIVILEGE_QUERIES:
            query = q.query
            target = q.target
            print(f"Running query - {query}")
            resp = answer(query, identity, defense_config=conf, only_urr=True)

            # Visualizza chunks recuperati
            print_chunks(resp.sources, identity)

            # Chunk non autorizzati che vengono recuperati
            unauthorized_chunks = [
                s.source
                for s in resp.sources
                if not authorize_chunk(
                    {
                        "access_rank": s.access_rank,
                        "allowed_roles": s.allowed_roles or "",
                    },
                    identity,
                ).is_authorized
            ]

            sum_unauth = sum(1 for s in unauthorized_chunks)

            rows.append(
                {
                    "config": conf.label,
                    "iar": conf.iar,
                    "query_firewall": conf.query_firewall,
                    "output_filter": conf.output_filter,
                    "query": query,
                    "target": target,
                    "n_unauthorized_chunks": sum_unauth,  # Numero di chunk non autorizzati recuperati
                    "unauthorized_chunks": "|".join(
                        unauthorized_chunks
                    ),  # Chunk non autorizzati
                    "retrieved_chunks": len(
                        resp.sources
                    ),  # Numero totale di chunk recuperati
                }
            )

    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    # URR per config = somma numeratori / somma denominatori (livello documento).
    from collections import defaultdict

    num, den = defaultdict(int), defaultdict(int)
    for r in rows:
        num[r["config"]] += r["n_unauthorized_chunks"]
        den[r["config"]] += r["retrieved_chunks"]
    print("\n=== URR per configurazione ===")
    for c in sorted(num, key=lambda x: int(x[1:])):
        urr = num[c] / den[c] if den[c] else None
        print(
            f"  {c}: URR={urr:.3f}" if urr is not None else f"  {c}: URR=n/a (0 chunk)"
        )


def print_chunks(sources: dict, identity: UserIdentity):
    for i, src in enumerate(sources, start=1):

        is_dict = isinstance(src, dict)
        source_name = src.get("source") if is_dict else getattr(src, "source", "N/A")
        category = src.get("category") if is_dict else getattr(src, "category", "N/A")
        score = src.get("score") if is_dict else getattr(src, "score", 0.0)
        access_level = (
            src.get("access_level") if is_dict else getattr(src, "access_level", "N/A")
        )
        roles = (
            src.get("allowed_roles")
            if is_dict
            else getattr(src, "allowed_roles", "N/A")
        )
        secrets = (
            src.get("contains_secrets")
            if is_dict
            else getattr(src, "contains_secrets", False)
        )
        preview = (
            src.get("text_preview") if is_dict else getattr(src, "text_preview", "")
        )

        # Pulisce i ritorni a capo per non rompere l'impaginazione
        clean_preview = preview.replace("\n", " ").strip()
        print(f"  [{i}] File: {source_name}")
        print(f"      Category: {category} | Score: {score:.4f} | Secrets: {secrets}")
        print(f"      Access: {access_level} | Roles: {roles}")
        print(f"      Preview: {clean_preview[:120]}...")
        authorized = authorize_chunk(
            {
                "access_rank": src.access_rank,
                "allowed_roles": src.allowed_roles or "",
            },
            identity,
        ).is_authorized

        print(f"      Authorized: {authorized}")
        print("      " + "-" * 40)


if __name__ == "__main__":
    run_urr()
