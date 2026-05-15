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
# LLM servito localmente da Ollama
LLM_MODEL = "llama3.1:8b"
LLM_REQUEST_TIMEOUT = 120.0  # secondi, generoso per CPU/Metal

# Modello di embedding (locale, scaricato da HuggingFace al primo uso)
# BGE-small: 384 dimensioni, ottimo rapporto qualità/peso, citato nella tesi
EMBED_MODEL = "BAAI/bge-small-en-v1.5"

# --- Parametri RAG ---
CHUNK_SIZE = 512            # token per chunk
CHUNK_OVERLAP = 64          # overlap tra chunk consecutivi
SIMILARITY_TOP_K = 4        # quanti chunk recuperare per ogni query

# --- Vector DB ---
CHROMA_COLLECTION = "cloud_corpus"