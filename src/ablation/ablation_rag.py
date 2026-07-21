"""
RAG che implementa Identity-Aware Retrieval

C0 = nessuna difesa
C1 = query firewall (difese singole)
C2 = iar (difese singole)
C3 = output filter (difese singole)
C4 = query firewall, iar (coppie)
C5 = query firewall, output filter (coppie)
C6 = iar, output filter (coppie)
C7 = query firewall, iar, output filter (pipeline di difesa completa)

"""

import logging
import sys
from typing import Optional

from llama_index.core import Settings, StorageContext, VectorStoreIndex
from llama_index.core.response_synthesizers import get_response_synthesizer
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.vector_stores.chroma import ChromaVectorStore

import chromadb
from pydantic import BaseModel

from src import config
from src.IAR.identity import DEFAULT_USER, UserIdentity
from src.IAR.retriever import IdentityAwareRetriever

from src.ablation.ablation_configs import CONFIGS, DefenceConfig

from src.query_firewall.query_firewall import DEFAULT_QUERY_FIREWALL

from src.output_filter.output_filter import DEFAULT_OUTPUT_FILTER

log = logging.getLogger("ablation_rag")

_index_cache: Optional[VectorStoreIndex] = None


def load_index() -> VectorStoreIndex:
    """Carica l'indice creato da ingest.py mantentendo una cache globale per evitare di ricaricarlo ad ogni richiesta."""
    global _index_cache

    if _index_cache is None:
        # Qui dovresti implementare la logica per caricare l'indice

        Settings.embed_model = HuggingFaceEmbedding(
            model_name=config.EMBED_MODEL
        )  # Carica embedding model
        Settings.llm = Ollama(
            model=config.LLM_MODEL, request_timeout=config.LLM_REQUEST_TIMEOUT
        )  # Carica llm

        chroma_client = chromadb.PersistentClient(
            path=str(config.CHROMA_DIR)
        )  # Carica ChromaDB
        chroma_collection = chroma_client.get_collection(
            config.CHROMA_COLLECTION
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


class SourceInfo(BaseModel):
    source: str
    category: str
    score: Optional[float]
    text_preview: str
    access_level: Optional[str] = None
    access_rank: Optional[int] = None
    allowed_roles: Optional[str] = None
    contains_secrets: Optional[bool] = None


class AuditEntry(BaseModel):
    source: str
    access_level: str
    allowed_roles: str
    contains_secrets: bool
    score: Optional[float]
    authorized: Optional[bool] = None
    reason: Optional[str] = None


class AblationQueryResponse(BaseModel):
    query: str
    identity: dict
    answer: str
    sources: list[SourceInfo]
    audit_log: list[AuditEntry]
    stats: dict
    defence_config: DefenceConfig


def answer(
    query: str,
    identity: UserIdentity = DEFAULT_USER,
    defense_config: DefenceConfig = CONFIGS["C7"],
    top_k: int = config.SIMILARITY_TOP_K,
    only_urr: Optional[
        bool
    ] = False,  # Settare a True per evitare la generazione LLM non necessaria per la misurazione del URR
) -> AblationQueryResponse:
    """Esegue una query RAG completa e restituisce riposta e contesto filtrato in base all'identità dell'utente."""

    # Se query firewall è attivo e la query viene bloccata ritorna la risposta bloccata
    if defense_config.query_firewall and DEFAULT_QUERY_FIREWALL.inspect(query).blocked:
        return _blocked_response(query, identity, top_k, defense_config=defense_config)

    index = load_index()

    # Se iar è attivo applica Identity Aware Retrival altrimenti il retrieval standard
    if defense_config.iar:
        result = IdentityAwareRetriever(index, top_k).retrieve(query, identity)
        chunks = result.chunks

    else:
        chunks = index.as_retriever(similarity_top_k=top_k).retrieve(query)

    # Verifica chunks per la generazione della risposta
    if len(chunks) == 0:
        log.warning(
            "Post filtering context is empty for query '%s' and identity '%s'. Returning standard response.",
            query,
            identity,
        )

        llm_answer = (
            "Unable to provide an answer to the query with the recovered sources."
        )

    else:
        if not only_urr:
            synthesizer = get_response_synthesizer()
            llm_answer = str(synthesizer.synthesize(query, nodes=chunks))
        else:
            llm_answer = "Answer not generated for URR measurements"

    # Se output filter è attivo allora filtra la risposta generata
    if defense_config.output_filter:
        filtered_result = DEFAULT_OUTPUT_FILTER.scan(llm_answer)

        llm_answer = filtered_result.redacted_text

    retrieved_with_secrets = sum(
        1 for n in chunks if (n.metadata or {}).get("contains_secrets")
    )

    return AblationQueryResponse(
        query=query,
        identity={
            "user_id": identity.user_id,
            "role": identity.role,
            "access_level": identity.access_level.value,
        },
        answer=llm_answer,
        sources=[
            {
                "source": node.metadata.get("source"),
                "category": node.metadata.get("category"),
                "score": float(node.score) if node.score is not None else None,
                "text_preview": node.text[:200],
                "access_level": node.metadata.get("access_level", None),
                "access_rank": node.metadata.get("access_rank", None),
                "allowed_roles": node.metadata.get("allowed_roles", None),
                "contains_secrets": node.metadata.get("contains_secrets", None),
            }
            for node in chunks
        ],
        audit_log=[
            {
                "source": (node.metadata or {}).get("source", "unknown"),
                "access_level": (node.metadata or {}).get("access_level", ""),
                "allowed_roles": (node.metadata or {}).get("allowed_roles", ""),
                "contains_secrets": bool(
                    (node.metadata or {}).get("contains_secrets", False)
                ),
                "score": float(node.score) if node.score is not None else None,
            }
            for node in chunks
        ],
        stats={
            "retrieved": len(chunks),
            "retrieved_with_secrets": retrieved_with_secrets,
            "top_k_requested": top_k,
        },
        defence_config=defense_config,
    )


def _blocked_response(
    query: str, identity: UserIdentity, top_k: int, defense_config: DefenceConfig
) -> AblationQueryResponse:
    return AblationQueryResponse(
        query=query,
        identity={
            "user_id": identity.user_id,
            "role": identity.role,
            "access_level": identity.access_level.value,
        },
        answer="Unable to provide an answer due to security restrictions applied to the request.",
        sources=[],
        audit_log=[],
        stats={
            "retrieved": 0,
            "retrieved_with_secrets": 0,
            "top_k_requested": top_k,
        },
        defence_config=defense_config,
    )


def ablation_study(
    query: str, user_identity: UserIdentity
) -> list[AblationQueryResponse]:
    results_configs: list[AblationQueryResponse] = []
    for conf in CONFIGS.values():
        print(
            f"---- Executing CONF-{conf.label} (QF: {conf.query_firewall}, IAR: {conf.iar}, OF: {conf.output_filter}) ----"
        )
        result = answer(query, user_identity, defense_config=conf)

        # TODO: Esegue il dataset di query appartenente ad un determinato asse di attacco

        results_configs.append(result)

    return results_configs


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Use: python -m src.ablation.ablation_rag "your request"')
        sys.exit(1)

    user_identity = UserIdentity(user_id="user_developer", role="developer")

    results_ablation = ablation_study(sys.argv[1], user_identity)

    # STAMPA I RISULTATI
    print("\n" + "=" * 40)
    print("=== RISULTATI ABLATION STUDY ===")
    print("=" * 40)

    for res in results_ablation:
        print(
            f"\n[{res.defence_config.label.upper()}] - (QF: {res.defence_config.query_firewall}, IAR: {res.defence_config.iar}, OF: {res.defence_config.output_filter})"
        )
        print(f"Query: {res.query}")
        print(f"Answer: {res.answer}")
        print(f"Stats: {res.stats}")
        print(f"\nAuthorized Sources ({len(res.sources)}):")
        for i, src in enumerate(res.sources, start=1):

            is_dict = isinstance(src, dict)
            source_name = (
                src.get("source") if is_dict else getattr(src, "source", "N/A")
            )
            category = (
                src.get("category") if is_dict else getattr(src, "category", "N/A")
            )
            score = src.get("score") if is_dict else getattr(src, "score", 0.0)
            access_level = (
                src.get("access_level")
                if is_dict
                else getattr(src, "access_level", "N/A")
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
            print(
                f"      Category: {category} | Score: {score:.4f} | Secrets: {secrets}"
            )
            print(f"      Access: {access_level} | Roles: {roles}")
            print(f"      Preview: {clean_preview[:120]}...")
            print("      " + "-" * 40)

        print("=" * 60)
