"""
API HTTP del sistema RAG.

Eseguibile con: uvicorn src.api.api:app --reload --port 8000

Documentazione interattiva: http://localhost:8000/docs
"""

import logging
from contextlib import asynccontextmanager
from typing import Optional

import chromadb
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from llama_index.core import Settings, StorageContext, VectorStoreIndex
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.vector_stores.chroma import ChromaVectorStore
from pydantic import BaseModel, Field

from src import project_settings
from src.iar.identity import UserIdentity, ROLE_TO_ACCESS_LEVEL
from src.rag.rag_secure import answer as answer_secure, SecureQueryResponse

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger("api")

# Stato globale (caricato una volta sola all'avvio)

# L'idea è che caricare l'indice e l'LLM è costoso (download/load di vari
# modelli, apertura del DB, ecc.). Vogliamo farlo UNA VOLTA sola all'avvio
# del server, non ad ogni richiesta. Per questo usiamo un "lifespan" context.
state: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inizializza l'indice all'avvio, lo distrugge alla chiusura."""
    log.info("Avvio: carico modello di embedding %s", project_settings.EMBED_MODEL)
    Settings.embed_model = HuggingFaceEmbedding(
        model_name=project_settings.EMBED_MODEL,
        query_instruction="Represent this sentence for searching relevant passages:",  # Su consiglio di huggingface
    )  # Carica embedding model

    log.info("Avvio: configuro LLM %s via Ollama", project_settings.LLM_MODEL)
    Settings.llm = Ollama(
        model=project_settings.LLM_MODEL,
        request_timeout=project_settings.LLM_REQUEST_TIMEOUT,
    )

    log.info("Avvio: apro ChromaDB in %s", project_settings.CHROMA_DIR)
    chroma_client = chromadb.PersistentClient(path=str(project_settings.CHROMA_DIR))
    chroma_collection = chroma_client.get_collection(project_settings.CHROMA_COLLECTION)
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    state["index"] = VectorStoreIndex.from_vector_store(
        vector_store=vector_store,
        storage_context=storage_context,
    )
    state["chunk_count"] = chroma_collection.count()
    log.info("Avvio completato. Chunks in collection: %d", state["chunk_count"])

    yield

    log.info("Shutdown")
    state.clear()


app = FastAPI(
    title="Secure RAG — Cloud Assistant",
    description="Prototipo per studio sicurezza RAG (tesi)",
    version="0.1.0",
    lifespan=lifespan,
)

# Configurazione CORS per accettare le preflight OPTIONS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*"
    ],  # In produzione, metti l'URL esatto (es. "http://localhost:3000")
    allow_credentials=True,
    allow_methods=["*"],  # Autorizza tutti i metodi, incluso OPTIONS e POST
    allow_headers=["*"],  # Autorizza Content-Type
)


# Request/Response types
class QueryRequest(BaseModel):
    """Payload di una richiesta di query."""

    query: str = Field(..., min_length=1, description="La domanda dell'utente")
    top_k: Optional[int] = Field(
        default=None,
        ge=1,
        le=20,
        description="Numero di chunk da recuperare (default: config.SIMILARITY_TOP_K)",
    )
    # Placeholder per il futuro Identity-Aware Retrieval.
    # Per ora non viene usato: lo accettiamo già nello schema per non dover
    # rompere la compatibilità quando lo implementeremo.
    user_role: Optional[str] = Field(
        default=None,
        description="Ruolo dell'utente (admin/developer/public). NON ANCORA APPLICATO.",
    )


@app.get("/")
def root() -> dict:
    """Info di base sul servizio."""
    return {
        "service": "secure-rag",
        "status": "running",
        "chunks_indexed": state.get("chunk_count", 0),
        "llm": project_settings.LLM_MODEL,
        "embed_model": project_settings.EMBED_MODEL,
    }


@app.get("/health")
def health() -> dict:
    """Health check semplice."""
    if "index" not in state:
        raise HTTPException(status_code=503, detail="Index not loaded")
    return {"status": "ok"}


# Punto di ingresso per l'utilizzo del sistema
@app.post("/query", response_model=SecureQueryResponse)
def secure_query_endpoint(req: QueryRequest) -> SecureQueryResponse:
    """Esegue una query con IAR pre retrieval."""

    if "index" not in state:
        raise HTTPException(status_code=503, detail="Index not loaded")

    role = (req.user_role or "public").strip().lower()
    if role not in ROLE_TO_ACCESS_LEVEL:
        raise HTTPException(
            status_code=400,
            detail=f"Ruolo utente non valido: {role}. Ruoli validi: {list(ROLE_TO_ACCESS_LEVEL.keys())}",
        )

    identity = UserIdentity(user_id=f"user_{role}", role=role)

    top_k = req.top_k or project_settings.SIMILARITY_TOP_K
    log.info("Query (top_k=%d, user_role=%s): %s", top_k, role, req.query)

    result = answer_secure(
        query=req.query,
        identity=identity,
        top_k=top_k,
        index=state["index"],
    )

    return SecureQueryResponse(
        query=result.query,
        identity=result.identity,
        answer=result.answer,
        sources=result.sources,
        audit_log=result.audit_log,
        stats=result.stats,
    )
