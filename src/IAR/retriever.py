"""
Identity-Aware Retriever.

Il predicato di autorizzazione è tradotto in un filtro sui metadati applicato dal db vettoriale prima del retrieval semantico. In questo modo l'utente riceve solo chunk di documenti per cui possiede l'autorizzazione.

Funzionamento :
    1. Applica il filtro sui metadati del db vettoriale prima del recupero.
    2. Esegue il retrieval standard sul vector store (top-k semantico sui documenti autorizzati).
    3. Ritorna i risultati
"""

from dataclasses import dataclass, field
from typing import Optional

from llama_index.core import VectorStoreIndex
from llama_index.core.schema import NodeWithScore

from src.IAR.identity import UserIdentity, authorize_chunk, authorization_filter

class AuthorizationError(RuntimeError):
    """ Eccezione lanciata se il vector store restituisce un chunk che non è autorizzato.
    
    Scatta solo se il filtro non è stato applicato correttamente. Caso d'uso non previsto."""

@dataclass
class RetrievalRecord:
    """ Singolo record del retrieval, informazioni del chunk recuperato"""
    source: str
    access_level: str
    allowed_roles: str
    contains_secrets: bool
    score: Optional[float]
    text_preview: str

@dataclass
class RetrievalResult:
    """ Risultato del retrieval basato su identità"""
    identity: UserIdentity
    chunks: list[NodeWithScore] # Tutti i top-k chunks recuperati dal db vettoriale
    audit_log: list[RetrievalRecord] = field(default_factory=list) 

    @property
    def retrieved_count(self) -> int:
        """ Numero di chunk recuperati"""
        return len(self.chunks)
    
    @property
    def chunks_with_secrets(self) -> int:
        """ Numero di chunk recuperati che contengono segreti"""
        return sum(1 for record in self.audit_log if record.contains_secrets)
    

class IdentityAwareRetriever:
    """ Retriever ristretto al sottospazio dei chunk autorizzati per l'identità che effettua la richiesta"""

    def __init__(self, index: VectorStoreIndex, top_k: int):
        self._index = index
        self._top_k = top_k

    def retrieve(self, query: str, identity: UserIdentity) -> RetrievalResult:

        # Applicazione del filtro 
        filters = authorization_filter(identity)

        # Retrieval sematico standard (top-k)
        retriever = self._index.as_retriever(
            similarity_top_k=self._top_k, 
            filters=filters
        )
        
        chunks: list[NodeWithScore] = retriever.retrieve(query)

        # Verifica se il filtro è stato applicato correttamente
        violations = [
            (chunk.metadata or {}).get("source")
            for chunk in chunks if not authorize_chunk(chunk.metadata or {}, identity).is_authorized
        ]

        # Non dovrebbe mai essere lanciata
        if violations:
            raise AuthorizationError(
                f"Il vector store ha restituito {len(violations)} chunk non "
                f"autorizzati per il ruolo '{identity.role}': {violations}. "
                f"Il filtro pre-retrieval non è stato applicato correttamente."
            )
        
        audit_log = [
            RetrievalRecord(
                source=(chunk.metadata).get("source", "unknown"),
                access_level=(chunk.metadata or {}).get("access_level", ""),
                allowed_roles=(chunk.metadata or {}).get("allowed_roles", ""),
                contains_secrets=bool((chunk.metadata or {}).get("contains_secrets", False)),
                score=float(chunk.score) if chunk.score is not None else None,
                text_preview=chunk.text[:200],
            )
            for chunk in chunks
        ]

        return RetrievalResult(
            identity=identity,
            chunks=chunks,
            audit_log=audit_log,
        )




