"""
Ingest pipeline: legge il corpus, crea embeddings, popola ChromaDB.

Eseguibile con:
    python -m src.ingest
"""
import logging
import shutil
from pathlib import Path

import chromadb
from llama_index.core import (
    SimpleDirectoryReader,
    StorageContext,
    VectorStoreIndex,
    Settings,
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore

from src import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("ingest")


def build_index(reset: bool = True) -> VectorStoreIndex:
    """Costruisce (o ricostruisce) l'indice vettoriale dal corpus."""
    # 1. Reset opzionale dello storage. Comodo in fase di sviluppo:
    #    cambiare il corpus e voler ripartire puliti è all'ordine del giorno.
    if reset and config.CHROMA_DIR.exists():
        log.info("Reset dello storage esistente in %s", config.CHROMA_DIR)
        shutil.rmtree(config.CHROMA_DIR)
    config.CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    # 2. Configurazione globale di LlamaIndex (Settings è singleton-like).
    #    Specifichiamo l'embedding model e disabilitiamo l'LLM (qui non serve:
    #    stiamo solo indicizzando, non generando).
    log.info("Carico il modello di embedding: %s", config.EMBED_MODEL)
    Settings.embed_model = HuggingFaceEmbedding(model_name=config.EMBED_MODEL)
    Settings.llm = None
    Settings.chunk_size = config.CHUNK_SIZE
    Settings.chunk_overlap = config.CHUNK_OVERLAP

    # 3. Setup ChromaDB persistente su disco.
    chroma_client = chromadb.PersistentClient(path=str(config.CHROMA_DIR))
    chroma_collection = chroma_client.get_or_create_collection(
        name=config.CHROMA_COLLECTION
    )
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    # 4. Lettura ricorsiva del corpus.
    log.info("Leggo i documenti da %s", config.CORPUS_DIR)
    reader = SimpleDirectoryReader(
        input_dir=str(config.CORPUS_DIR),
        recursive=True,
        required_exts=[".txt", ".md", ".json", ".yaml", ".yml", ".env", ".log"],
        filename_as_id=True,
    )
    documents = reader.load_data()
    log.info("Caricati %d documenti", len(documents))

    # 5. Aggiungiamo metadati utili a ciascun documento.
    #    Per ora ricaviamo la "categoria" dal nome della sottocartella.
    #    Questo è il PRIMO PASSO verso l'Identity-Aware Retrieval (Sezione 8.A
    #    della tesi): più avanti aggiungeremo "access_level" qui.
    for doc in documents:
        rel_path = Path(doc.metadata["file_path"]).relative_to(config.CORPUS_DIR)
        category = rel_path.parts[0] if len(rel_path.parts) > 1 else "misc"
        doc.metadata["category"] = category
        doc.metadata["source"] = str(rel_path)

    # 6. Chunking + embedding + indicizzazione (LlamaIndex fa tutto in una riga).
    splitter = SentenceSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
    )
    log.info("Indicizzo i documenti (chunking + embedding)...")
    index = VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
        transformations=[splitter],
        show_progress=True,
    )

    log.info("Indice creato. Chunks totali in collection: %d", chroma_collection.count())
    return index


if __name__ == "__main__":
    build_index(reset=True)