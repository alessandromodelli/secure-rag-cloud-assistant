"""
Motore RAG: data una query, recupera contesto rilevante e genera una risposta.

Esegui con:
    python -m src.rag.rag "La tua domanda qui"
"""

import logging
import sys

from llama_index.core import get_response_synthesizer

from src import project_settings
from src.ingest.load_index import load_index

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger("rag")


def answer(query: str, top_k: int = project_settings.SIMILARITY_TOP_K) -> dict:
    """Esegue una query RAG completa e ritorna risposta + contesto."""
    index = load_index()
    # query_engine = index.as_query_engine(similarity_top_k=top_k)
    # log.info("Query: %s", query)
    # response = query_engine.query(query)

    # Recupera i chunks semanticamente simili alla query (rappresentazione vettoriale)
    retriever = index.as_retriever(similarity_top_k=top_k)
    chunks = retriever.retrieve(query)

    # I chunk recuperati vengono passati come contesto al LLM insieme alla query
    synthesizer = get_response_synthesizer()
    llm_answer = str(synthesizer.synthesize(query, nodes=chunks))

    # Estraiamo le fonti per trasparenza (utile in tesi: ogni risposta è
    # tracciabile ai chunk che l'hanno generata).
    sources = [
        {
            "source": node.metadata.get("source", "unknown"),
            "category": node.metadata.get("category", "unknown"),
            "score": float(node.score) if node.score is not None else None,
            "text_preview": node.text[:200],
            "access_level": node.metadata.get("access_level", None),
            "allowed_roles": node.metadata.get("allowed_roles", None),
            "contains_secrets": node.metadata.get("contains_secrets", None),
        }
        for node in chunks
    ]

    return {
        "query": query,
        "answer": llm_answer,
        "sources": sources,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Uso: python -m src.rag.rag "la tua domanda"')
        sys.exit(1)

    result = answer(sys.argv[1])
    print("\n=== RISPOSTA ===")
    print(result["answer"])
    print("\n=== FONTI RECUPERATE ===")
    for i, s in enumerate(result["sources"], start=1):
        print(
            f"[{i}] {s['source']}  (category={s['category']}, score={s['score']:.3f})"
        )
        print(f"    {s['text_preview']!r}")
