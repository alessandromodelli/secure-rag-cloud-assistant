"""
Ingest pipeline: legge il corpus, crea embeddings, popola ChromaDB.

Eseguibile con:
    python -m src.ingest.ingest
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

from src.ingest.metadata import DocumentMetadata, KNOWN_ROLES, Origin

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger("ingest")


def build_index(
    reset: bool = True,
    collection_name: str = config.CHROMA_COLLECTION,
    include_poisoned: bool = False,
) -> VectorStoreIndex:
    """Costruisce (o ricostruisce) l'indice vettoriale dal corpus.

    include_poisoned=False  -> corpus pulito (asse di attacchi Privilege Escalation e Secret Leakage)
    include_poisoned=True   -> corpus avvelenato  (asse Poisoning)
    """

    config.CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    chroma_client = chromadb.PersistentClient(path=str(config.CHROMA_DIR))

    # 1. Reset opzionale dello storage. Rimuove collection senza eliminare l'intera cartella
    if reset:
        try:
            chroma_client.delete_collection(collection_name)
            log.info("Collection '%s' rimossa", collection_name)
        except Exception:
            pass  # non esisteva

    # 2. Configurazione globale di LlamaIndex.
    #    Set dell'embedding model e disattivazione LLM visto che non è necessario per l'indicizzazione.
    log.info("Carico il modello di embedding: %s", config.EMBED_MODEL)
    Settings.embed_model = HuggingFaceEmbedding(model_name=config.EMBED_MODEL)
    Settings.llm = None
    Settings.chunk_size = config.CHUNK_SIZE
    Settings.chunk_overlap = config.CHUNK_OVERLAP

    # 3. Setup ChromaDB.
    chroma_collection = chroma_client.get_or_create_collection(name=collection_name)
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
            log.warning(
                "Sidecar mancante per %s — documento SALTATO. "
                "Lancia `python -m src.validate_corpus` per dettagli.",
                file_path.name,
            )
            skipped += 1
            continue

        try:
            raw = json.loads(sidecar.read_text(encoding="utf-8"))
            meta = DocumentMetadata(**raw)
        except (json.JSONDecodeError, ValidationError) as e:
            log.warning(
                "Metadati invalidi per %s (%s) — documento SALTATO.",
                file_path.name,
                type(e).__name__,
            )
            skipped += 1
            continue

        # I documenti adversarial entrano solo nella collection avvelenata.
        if meta.origin is Origin.POISONED and not include_poisoned:
            continue
        # Denormalizzazione dei ruoli.
        # Se allowed_roles è vuoto, significa che tutti i ruoli con un valido access_level sono autorizzati.
        effective_roles = (
            set(meta.allowed_roles) if meta.allowed_roles else set(KNOWN_ROLES)
        )
        unknown = effective_roles - set(KNOWN_ROLES)
        if unknown:
            log.warning(
                "Ruoli ignoti nell'ACL di %s: %s — documento SALTATO.",
                meta.source,
                sorted(unknown),
            )
            skipped += 1
            continue
        role_flags = {
            f"role_{r}": int(r in effective_roles) for r in sorted(KNOWN_ROLES)
        }

        doc.metadata.update(
            {
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
                **role_flags,
            }
        )

        # Rimozione dei metadati di controllo dall'embedding e dall'LLM, che non devono essere indicizzati.
        control_keys = [
            "file_path",
            "access_level",
            "access_rank",
            "allowed_roles",
            "sensitivity",
            "contains_secrets",
            "ground_truth",
            "origin",
            *role_flags,
        ]
        doc.excluded_embed_metadata_keys = list(
            dict.fromkeys([*doc.excluded_embed_metadata_keys, *control_keys])
        )
        doc.excluded_llm_metadata_keys = list(
            dict.fromkeys([*doc.excluded_llm_metadata_keys, *control_keys])
        )

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

    log.info(
        "Indice creato. Chunks totali in collection: %d", chroma_collection.count()
    )
    return index


if __name__ == "__main__":
    import sys

    if "--poisoned" in sys.argv:
        build_index(
            reset=True,
            collection_name=config.CHROMA_COLLECTION_POISONED,
            include_poisoned=True,
        )
    else:
        build_index(reset=True)
