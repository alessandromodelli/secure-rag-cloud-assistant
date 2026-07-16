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

import json
from pathlib import Path

from pydantic import ValidationError

from src.ingest.metadata import DocumentMetadata

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

    # 4. Lettura del corpus.
    log.info("Leggo i documenti da %s", config.CORPUS_DIR)
    reader = SimpleDirectoryReader(
        input_dir=str(config.CORPUS_DIR),
        recursive=True,
        required_exts=[".txt", ".md", ".json", ".yaml", ".yml", ".env", ".log"],
        filename_as_id=True,
    )
    documents = reader.load_data()
    log.info("Caricati %d documenti", len(documents))

    # 5. Caricamento dei metadati dai .meta.json
    #    Saltando i sidecar stessi visto che non sono documenti da indicizzare.
    log.info("Carico i metadati dai .meta.json")
    valid_documents = []
    skipped = 0
    for doc in documents:
        file_path = Path(doc.metadata["file_path"])

        # Salta i .meta.json: arrivano dal SimpleDirectoryReader perché .json
        # è nelle required_exts, ma non vanno indicizzati.
        if file_path.name.endswith(".meta.json"):
            continue

        sidecar = file_path.with_name(file_path.name + ".meta.json")
        if not sidecar.exists():
            log.warning("Sidecar mancante per %s — documento SALTATO. "
                        "Lancia `python -m src.validate_corpus` per dettagli.",
                        file_path.name)
            skipped += 1
            continue

        try:
            raw = json.loads(sidecar.read_text(encoding="utf-8"))
            meta = DocumentMetadata(**raw)
        except (json.JSONDecodeError, ValidationError) as e:
            log.warning("Metadati invalidi per %s (%s) — documento SALTATO.",
                        file_path.name, type(e).__name__)
            skipped += 1
            continue

        # Iniettiamo i metadati nel documento di LlamaIndex.
        # ChromaDB richiede valori primitivi (str/int/float/bool) nei metadati,
        # quindi serializziamo le liste come stringhe CSV.
        doc.metadata.update({
            "source": meta.source,
            "category": meta.category,
            "doc_type": meta.doc_type.value,
            "access_level": meta.access_level.value,
            "access_rank": meta.access_level.rank,
            "allowed_roles": ",".join(meta.allowed_roles),
            "sensitivity": meta.sensitivity.value,
            "contains_secrets": meta.contains_secrets,
            "ground_truth": meta.ground_truth or "",
            "origin": meta.origin.value,
        })
        valid_documents.append(doc)

    if skipped > 0:
        log.warning("%d documenti saltati per problemi di metadati.", skipped)
    log.info("Documenti pronti per l'indicizzazione: %d", len(valid_documents))
    documents = valid_documents  # sovrascrittura lista dei documenti validi


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