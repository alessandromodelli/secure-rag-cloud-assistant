"""
API HTTP del sistema RAG.

Eseguibile con:
    uvicorn src.api:app --reload --port 8000

Documentazione interattiva: http://localhost:8000/docs
"""
import logging
from contextlib import asynccontextmanager
from typing import Optional

import chromadb
from fastapi import FastAPI, HTTPException
from llama_index.core import Settings, StorageContext, VectorStoreIndex
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.vector_stores.chroma import ChromaVectorStore
from pydantic import BaseModel, Field

from src import config
from src.IAR.identity import DEFAULT_USER, UserIdentity, ROLE_TO_ACCESS_LEVEL
from src.RAG.secure_rag_pf import answer as secure_answer_post_filter
from src.RAG.secure_rag import answer as secure_answer




logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("api")

# Stato globale (caricato una volta sola all'avvio)

# L'idea è che caricare l'indice e l'LLM è costoso (download/load di vari
# modelli, apertura del DB, ecc.). Vogliamo farlo UNA VOLTA sola all'avvio
# del server, non ad ogni richiesta. Per questo usiamo un "lifespan" context.
state: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inizializza l'indice all'avvio, lo distrugge alla chiusura."""
    log.info("Avvio: carico modello di embedding %s", config.EMBED_MODEL)
    Settings.embed_model = HuggingFaceEmbedding(model_name=config.EMBED_MODEL)

    log.info("Avvio: configuro LLM %s via Ollama", config.LLM_MODEL)
    Settings.llm = Ollama(
        model=config.LLM_MODEL,
        request_timeout=config.LLM_REQUEST_TIMEOUT,
    )

    log.info("Avvio: apro ChromaDB in %s", config.CHROMA_DIR)
    chroma_client = chromadb.PersistentClient(path=str(config.CHROMA_DIR))
    chroma_collection = chroma_client.get_collection(config.CHROMA_COLLECTION)
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    state["index"] = VectorStoreIndex.from_vector_store(
        vector_store=vector_store,
        storage_context=storage_context,
    )
    state["chunk_count"] = chroma_collection.count()
    log.info("Avvio completato. Chunks in collection: %d", state["chunk_count"])

    yield  # qui l'app gira

    log.info("Shutdown")
    state.clear()


app = FastAPI(
    title="Secure RAG — Cloud Assistant",
    description="Prototipo per studio sicurezza RAG (tesi)",
    version="0.1.0",
    lifespan=lifespan,
)


# Request/Response types
class QueryRequest(BaseModel):
    """Payload di una richiesta di query."""
    query: str = Field(..., min_length=1, description="La domanda dell'utente")
    top_k: Optional[int] = Field(
        default=None,
        ge=1, le=20,
        description="Numero di chunk da recuperare (default: config.SIMILARITY_TOP_K)",
    )
    # Placeholder per il futuro Identity-Aware Retrieval.
    # Per ora non viene usato: lo accettiamo già nello schema per non dover
    # rompere la compatibilità quando lo implementeremo.
    user_role: Optional[str] = Field(
        default=None,
        description="Ruolo dell'utente (admin/developer/public). NON ANCORA APPLICATO.",
    )


class SourceInfo(BaseModel):
    source: str
    category: str
    score: Optional[float]
    text_preview: str
    access_level: Optional[str] = None
    allowed_roles: Optional[str] = None
    contains_secrets: Optional[bool] = None
    score: Optional[float]




class QueryResponse(BaseModel):
    query: str
    answer: str
    sources: list[SourceInfo]
    user_role: Optional[str] = None


class AuditEntry(BaseModel):
    source: str
    access_level: str
    allowed_roles: str
    contains_secrets: bool
    score: Optional[float]
    authorized: Optional[bool] = None
    reason: Optional[str] = None


class SecureQueryResponse(BaseModel):
    query: str
    identity: dict
    answer: str
    authorized_sources: list[SourceInfo]
    audit_log: list[AuditEntry]
    stats: dict

class SecureQueryIarResponse(BaseModel):
    query: str
    identity: dict
    answer: str
    authorized_sources: list[SourceInfo]
    audit_log: list[AuditEntry]
    stats: dict


# Endpoint

@app.get("/")
def root() -> dict:
    """Info di base sul servizio."""
    return {
        "service": "secure-rag",
        "status": "running",
        "chunks_indexed": state.get("chunk_count", 0),
        "llm": config.LLM_MODEL,
        "embed_model": config.EMBED_MODEL,
    }


@app.get("/health")
def health() -> dict:
    """Health check semplice."""
    if "index" not in state:
        raise HTTPException(status_code=503, detail="Index not loaded")
    return {"status": "ok"}


@app.post("/query", response_model=QueryResponse)
def query_endpoint(req: QueryRequest) -> QueryResponse:
    """Esegue una query RAG e ritorna risposta + fonti."""
    if "index" not in state:
        raise HTTPException(status_code=503, detail="Index not loaded")

    top_k = req.top_k or config.SIMILARITY_TOP_K
    log.info("Query (top_k=%d, user_role=%s): %s", top_k, req.user_role, req.query)

    query_engine = state["index"].as_query_engine(similarity_top_k=top_k)
    response = query_engine.query(req.query)

    sources = [
        SourceInfo(
            source=node.metadata.get("source", "unknown"),
            category=node.metadata.get("category", "unknown"),
            score=float(node.score) if node.score is not None else None,
            text_preview=node.text[:200],
            access_level=node.metadata.get("access_level", None),
            allowed_roles=node.metadata.get("allowed_roles", None).split(","),
            contains_secrets=node.metadata.get("contains_secrets", None),
        )
        for node in response.source_nodes
    ]

    return QueryResponse(
        query=req.query,
        answer=str(response),
        sources=sources,
        user_role=req.user_role,
    )



@app.post("/secure-query", response_model=SecureQueryResponse)
def secure_query_endpoint(req: QueryRequest) -> SecureQueryResponse:
    """ Esegue una query con Identity Aware Retrieval. Se il ruolo dell'utente non è specificato, viene usato il default (public)."""

    if "index" not in state: 
        raise HTTPException(status_code=503, detail="Index not loaded")
    
    role = (req.user_role or "public").strip().lower()
    if role not in ROLE_TO_ACCESS_LEVEL:
        raise HTTPException(status_code=400, detail=f"Ruolo utente non valido: {role}. Ruoli validi: {list(ROLE_TO_ACCESS_LEVEL.keys())}")
    
    identity = UserIdentity(user_id=f"user_{role}", role=role)

    top_k = req.top_k or config.SIMILARITY_TOP_K
    log.info("Query sicura (top_k=%d, user_role=%s): %s", top_k, role, req.query)

    result = secure_answer_post_filter(query=req.query, identity=identity, top_k=top_k)

    return SecureQueryResponse(**result)


@app.post("/secure_query_iar", response_model=SecureQueryIarResponse)
def secure_query_iar_endpoint(req: QueryRequest) -> SecureQueryIarResponse:
    """ Esegue una query con IAR pre retrieval. """

    if "index" not in state: 
        raise HTTPException(status_code=503, detail="Index not loaded")
    
    role = (req.user_role or "public").strip().lower()
    if role not in ROLE_TO_ACCESS_LEVEL:
        raise HTTPException(status_code=400, detail=f"Ruolo utente non valido: {role}. Ruoli validi: {list(ROLE_TO_ACCESS_LEVEL.keys())}")
    
    identity = UserIdentity(user_id=f"user_{role}", role=role)

    top_k = req.top_k or config.SIMILARITY_TOP_K
    log.info("Query sicura (top_k=%d, user_role=%s): %s", top_k, role, req.query)

    result = secure_answer(query=req.query, identity=identity, top_k=top_k)

    return SecureQueryIarResponse(**result)

