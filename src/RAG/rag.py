"""
Motore RAG: data una query, recupera contesto rilevante e genera una risposta.

Esegui con:
    python -m src.rag "La tua domanda qui"
"""
import logging
import sys

import chromadb
from llama_index.core import StorageContext, VectorStoreIndex, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.vector_stores.chroma import ChromaVectorStore

from src import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("rag")


def load_index() -> VectorStoreIndex:
    """Carica l'indice precedentemente creato da ingest.py."""
    Settings.embed_model = HuggingFaceEmbedding(model_name=config.EMBED_MODEL)
    Settings.llm = Ollama(
        model=config.LLM_MODEL,
        request_timeout=config.LLM_REQUEST_TIMEOUT,
    )

    chroma_client = chromadb.PersistentClient(path=str(config.CHROMA_DIR))
    chroma_collection = chroma_client.get_collection(config.CHROMA_COLLECTION)
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    index = VectorStoreIndex.from_vector_store(
        vector_store=vector_store,
        storage_context=storage_context,
    )
    return index


def answer(query: str, top_k: int = config.SIMILARITY_TOP_K) -> dict:
    """Esegue una query RAG completa e ritorna risposta + contesto."""
    index = load_index()
    query_engine = index.as_query_engine(similarity_top_k=top_k)

    log.info("Query: %s", query)
    response = query_engine.query(query)

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
            "contains_secrets":node.metadata.get("contains_secrets", None),
        }
        for node in response.source_nodes
    ]

    return {
        "query": query,
        "answer": str(response),
        "sources": sources,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python -m src.rag \"la tua domanda\"")
        sys.exit(1)

    result = answer(sys.argv[1])
    print("\n=== RISPOSTA ===")
    print(result["answer"])
    print("\n=== FONTI RECUPERATE ===")
    for i, s in enumerate(result["sources"], start=1):
        print(f"[{i}] {s['source']}  (category={s['category']}, score={s['score']:.3f})")
        print(f"    {s['text_preview']!r}")