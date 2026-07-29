import chromadb
from llama_index.vector_stores.chroma.base import _to_chroma_filter
from src import config
from src.IAR.identity import UserIdentity, ROLE_TO_ACCESS_LEVEL, authorization_filter

client = chromadb.PersistentClient(path=str(config.CHROMA_DIR))
coll = client.get_collection(config.CHROMA_COLLECTION)
k = config.SIMILARITY_TOP_K
print(f"corpus: {coll.count()} chunk   k={k}")
for role in sorted(ROLE_TO_ACCESS_LEVEL):
    ident = UserIdentity(user_id=f"m_{role}", role=role)
    n = len(coll.get(where=_to_chroma_filter(authorization_filter(ident)))["ids"])
    ratio = n / k
    flag = "DEGENERE" if n <= k else ("marginale" if ratio < 5 else "ok")
    print(f"  {role:<10} |A(s)|={n:<4} rapporto={ratio:.1f}  {flag}")
