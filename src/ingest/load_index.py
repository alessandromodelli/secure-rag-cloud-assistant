from typing import Optional

from llama_index.core import Settings, StorageContext, VectorStoreIndex
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.vector_stores.chroma import ChromaVectorStore

import chromadb
from src import project_settings

_index_cache: dict[str, VectorStoreIndex] = {}


def load_index(
    collection: str = project_settings.CHROMA_COLLECTION,
    temperature: Optional[float] = None,
) -> VectorStoreIndex:
    """Carica l'indice di una collection mantentendo una cache globale per evitare di ricaricarlo ad ogni richiesta."""
    if collection not in _index_cache:
        if not _index_cache:
            # Configurazione globale di Settings
            Settings.embed_model = HuggingFaceEmbedding(
                model_name=project_settings.EMBED_MODEL,
            )  # Carica embedding model

            # Parametri LLM
            llm_params = {
                "model": project_settings.LLM_MODEL,
                "request_timeout": project_settings.LLM_REQUEST_TIMEOUT,
            }

            # Aggiungi temperature solo se passata come parametro
            if temperature is not None:
                llm_params["temperature"] = temperature

            Settings.llm = Ollama(**llm_params)  # Carica llm

        chroma_client = chromadb.PersistentClient(
            path=str(project_settings.CHROMA_DIR)
        )  # Carica ChromaDB

        chroma_collection = chroma_client.get_collection(
            collection
        )  # Carica la collection ChromaDB
        vector_store = ChromaVectorStore(
            chroma_collection=chroma_collection
        )  # Crea il vector store
        storage_context = StorageContext.from_defaults(
            vector_store=vector_store
        )  # Crea il contesto di storage

        _index_cache[collection] = VectorStoreIndex.from_vector_store(
            vector_store=vector_store, storage_context=storage_context
        )  # Crea l'indice

    return _index_cache[collection]
