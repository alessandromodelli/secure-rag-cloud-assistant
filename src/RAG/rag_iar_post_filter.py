"""
RAG che implementa Identity-Aware Retrieval con filtraggio post recupero
"""

import logging
from typing import Optional

from llama_index.core import Settings, StorageContext, VectorStoreIndex
from llama_index.core.response_synthesizers import get_response_synthesizer
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.vector_stores.chroma import ChromaVectorStore

import chromadb

from src import project_settings
from src.IAR.identity import DEFAULT_USER, UserIdentity
from src.IAR.retriever_pf import IdentityAwareRetrieverPostFiltering, RetrievalResult

log = logging.getLogger("rag_iar_post_filter")

_index_cache: Optional[VectorStoreIndex] = None


def load_index() -> VectorStoreIndex:
    """Carica l'indice creato da ingest.py mantentendo una cache globale per evitare di ricaricarlo ad ogni richiesta."""
    global _index_cache

    if _index_cache is None:
        # Qui dovresti implementare la logica per caricare l'indice

        Settings.embed_model = HuggingFaceEmbedding(
            model_name=project_settings.EMBED_MODEL
        )  # Carica embedding model
        Settings.llm = Ollama(
            model=project_settings.LLM_MODEL,
            request_timeout=project_settings.LLM_REQUEST_TIMEOUT,
        )  # Carica llm

        chroma_client = chromadb.PersistentClient(
            path=str(project_settings.CHROMA_DIR)
        )  # Carica ChromaDB
        chroma_collection = chroma_client.get_collection(
            project_settings.CHROMA_COLLECTION
        )  # Carica la collection ChromaDB
        vector_store = ChromaVectorStore(
            chroma_collection=chroma_collection
        )  # Crea il vector store
        storage_context = StorageContext.from_defaults(
            vector_store=vector_store
        )  # Crea il contesto di storage

        _index_cache = VectorStoreIndex.from_vector_store(
            vector_store=vector_store, storage_context=storage_context
        )  # Crea l'indice

        return _index_cache

    return _index_cache


def answer(
    query: str,
    identity: UserIdentity = DEFAULT_USER,
    top_k: int = project_settings.SIMILARITY_TOP_K,
) -> dict:
    """Esegue una query RAG completa e restituisce riposta e contesto filtrato in base all'identità dell'utente."""

    index = load_index()
    retriever = IdentityAwareRetrieverPostFiltering(index=index, top_k=top_k)

    result: RetrievalResult = retriever.retrieve(query, identity)

    # Verifica che il contesto recuperato non sia vuoto dopo il filtraggio
    # Il contesto vuoto potrebbe far allucinare il modello, quindi in caso restituiamo una risposta standard,

    if not result.authorized_chunks:
        log.warning(
            "Contesto post filtraggio vuoto per query '%s' e identità '%s'. Restituisco risposta standard.",
            query,
            identity,
        )

        llm_answer = "Non è stato possibile rispondere alla domanda con le informazioni disponibili con il tuo livello di accesso. "

    else:
        # Se il contesto recuperato non risulta vuoto lo utilizziamo per generare la risposta con l'LLM

        synthesizer = get_response_synthesizer()
        response = synthesizer.synthesize(query, nodes=result.authorized_chunks)
        llm_answer = str(response)

    return {
        "query": query,
        "identity": {
            "user_id": identity.user_id,
            "role": identity.role,
            "access_level": identity.access_level.value,
        },
        "answer": llm_answer,
        "authorized_sources": [
            {
                "source": node.metadata.get("source"),
                "category": node.metadata.get("category"),
                "score": float(node.score) if node.score is not None else None,
                "text_preview": node.text[:200],
                "access_level": node.metadata.get("access_level", None),
                "allowed_roles": node.metadata.get("allowed_roles", None),
                "contains_secrets": node.metadata.get("contains_secrets", None),
            }
            for node in result.authorized_chunks
        ],
        "audit_log": [
            {
                "source": record.source,
                "access_level": record.access_level,
                "allowed_roles": record.allowed_roles,
                "contains_secrets": record.contains_secrets,
                "score": record.score,
                "authorized": record.decision.is_authorized,
                "reason": record.decision.reason,
            }
            for record in result.audit_log
        ],
        "stats": {
            "retrieved": len(result.raw_chunks),
            "authorized": len(result.authorized_chunks),
            "blocked": result.blocked_count,
            "blocked_with_secrets": result.blocked_count_with_secrets,
        },
    }
