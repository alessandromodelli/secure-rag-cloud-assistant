"""
Identity-Aware Retriever con filtraggio post recupero.

Funzionamento :
    1. Esegue il retrieval standard sul vector store (top-k semantico, non filtrato).
    2. Applica il filtro di autorizzazione a ciascun chunk (dopo il recupero).
    3. Ritorna sia la lista filtrata (per l'LLM) sia quella raw (per misurazione).
"""

from dataclasses import dataclass, field
from typing import Optional

from llama_index.core import VectorStoreIndex
from llama_index.core.schema import NodeWithScore

from src.iar.identity import UserIdentity, AuthorizationDecision, authorize_chunk


@dataclass
class RetrievalRecord:
    """Singolo record del retrieval, informazioni del chunk recuperato"""

    source: str
    access_level: str
    allowed_roles: str
    contains_secrets: bool
    score: Optional[float]
    text_preview: str
    decision: AuthorizationDecision


@dataclass
class RetrievalResult:
    """Risultato del retrieval basato su identità"""

    identity: UserIdentity
    raw_chunks: list[NodeWithScore]  # Tutti i top-k chunks recuperati dal db vettoriale
    authorized_chunks: list[NodeWithScore]  # Solo i chunk che superano l'autorizzazione
    audit_log: list[RetrievalRecord] = field(
        default_factory=list
    )  # Log di autorizzazione per ciascun chunk

    @property
    def blocked_count(self) -> int:
        """Numero di chunk bloccati che non hanno superato l'autorizzazione"""
        return len(self.raw_chunks) - len(self.authorized_chunks)

    @property
    def blocked_count_with_secrets(self) -> int:
        """Numero di chunk bloccati che contengono segreti"""
        return sum(
            1
            for record in self.audit_log
            if not record.decision.is_authorized and record.contains_secrets
        )


class IdentityAwareRetrieverPostFiltering:
    """Retriever che applica il filtro di autorizzazione in base all'identità dell'utente che effettua la richiesta"""

    def __init__(self, index: VectorStoreIndex, top_k: int):
        self._index = index
        self._top_k = top_k

    def retrieve(self, query: str, identity: UserIdentity) -> RetrievalResult:
        # Retrieval sematico standard (top-k)
        retriever = self._index.as_retriever(similarity_top_k=self._top_k)
        row_chunks: list[NodeWithScore] = retriever.retrieve(query)

        # Autorizzazione chunk per chunk
        authorized_chunks: list[NodeWithScore] = []
        audit_log: list[RetrievalRecord] = []

        for chunk in row_chunks:
            metadata = chunk.metadata or {}

            chunk_score = float(chunk.score) if chunk.score is not None else None
            decision = authorize_chunk(metadata, identity)

            audit_log.append(
                RetrievalRecord(
                    source=metadata.get("source", "unknown"),
                    access_level=metadata.get("access_level", ""),
                    allowed_roles=metadata.get("allowed_roles", ""),
                    contains_secrets=metadata.get("contains_secrets", False),
                    score=chunk_score,
                    text_preview=chunk.text[:200],
                    decision=decision,
                )
            )
            if decision.is_authorized:
                authorized_chunks.append(chunk)

        return RetrievalResult(
            identity=identity,
            raw_chunks=row_chunks,
            authorized_chunks=authorized_chunks,
            audit_log=audit_log,
        )
