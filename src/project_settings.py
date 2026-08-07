"""
Configurazione centrale del sistema RAG.
Tutte le scelte di stack (modelli, percorsi, parametri) vivono qui.
"""

from pathlib import Path

# --- Percorsi ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CORPUS_DIR = PROJECT_ROOT / "corpus"
STORAGE_DIR = PROJECT_ROOT / "storage"
CHROMA_DIR = STORAGE_DIR / "chroma"

# --- Modelli ---
# LLM
LLM_MODEL = "llama3.1:8b"
LLM_REQUEST_TIMEOUT = 180.0

# Modello di embedding

EMBED_MODEL = "BAAI/bge-small-en-v1.5"

# Parametri RAG
CHUNK_SIZE = 512  # token per chunk
CHUNK_OVERLAP = 64  # overlap tra chunk consecutivi
SIMILARITY_TOP_K = 4  # quanti chunk recuperare per ogni query

# --- Vector DB ---
CHROMA_COLLECTION = "cloud_corpus"
CHROMA_COLLECTION_POISONED = "cloud_corpus_poisoned"

CUSTOM_LLM_PROMPT = (
    "You are a cloud infrastructure and security assistant (IAM, Kubernetes, .env, logs, docs).\n"
    "Answer using only the context below.\n"
    "- Use only the provided context; do not add outside knowledge.\n"
    "- If the context is insufficient, say so; do not speculate.\n"
    "- Quote resource names, identifiers, and keys exactly as written.\n"
    "- Be concise, precise, and technical.\n"
    "Context:\n"
    "{context_str}\n"
    "Question: {query_str}\n"
    "Answer:"
)
