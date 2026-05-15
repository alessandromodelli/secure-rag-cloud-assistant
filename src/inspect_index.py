"""
Verifica che la collection ChromaDB sia popolata e mostra un assaggio.

Esegui con:
    python -m src.inspect_index
"""
import chromadb
from src import config


def main() -> None:
    client = chromadb.PersistentClient(path=str(config.CHROMA_DIR))
    coll = client.get_collection(config.CHROMA_COLLECTION)

    print(f"Collection: {coll.name}")
    print(f"Numero di chunk: {coll.count()}")
    print()

    # Mostriamo i primi 3 chunk con i loro metadati
    sample = coll.peek(limit=3)
    for i, (doc_id, text, meta) in enumerate(
        zip(sample["ids"], sample["documents"], sample["metadatas"]), start=1
    ):
        print(f"--- Chunk #{i} (id={doc_id}) ---")
        print(f"Metadata: {meta}")
        print(f"Text (primi 200 char): {text[:200]!r}")
        print()


if __name__ == "__main__":
    main()