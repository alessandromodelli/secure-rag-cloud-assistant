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
    sample = coll.peek(limit=5)
    for i, (doc_id, text, meta) in enumerate(
        zip(sample["ids"], sample["documents"], sample["metadatas"]), start=1
    ):
        print(f"--- Chunk #{i} (id={doc_id}) ---")
        print(f"  source           : {meta.get('source')}")
        print(f"  category/type    : {meta.get('category')} / {meta.get('doc_type')}")
        print(f"  access_level     : {meta.get('access_level')} (rank={meta.get('access_rank')})")
        print(f"  allowed_roles    : {meta.get('allowed_roles')}")
        print(f"  sensitivity      : {meta.get('sensitivity')}")
        print(f"  contains_secrets : {meta.get('contains_secrets')}")
        print(f"  ground_truth     : {meta.get('ground_truth')}")
        print(f"  origin           : {meta.get('origin')}")
        print(f"  text (200 char)  : {text[:200]!r}")
        print()


if __name__ == "__main__":
    main()