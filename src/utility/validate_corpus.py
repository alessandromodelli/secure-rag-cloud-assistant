"""
Validazione del corpus: ogni documento deve avere un file associato .meta.json conforme
allo schema. Da eseguire prima di ogni ingest.

Esegui con:
    python -m src.validate_corpus
"""

import json
import logging
import sys
from pathlib import Path

from pydantic import ValidationError

from src import project_settings
from src.ingest.metadata import DocumentMetadata, KNOWN_ROLES

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger("validate")

# Estensioni dei documenti reali (i file .meta.json NON sono documenti).
DOC_EXTENSIONS = {".txt", ".md", ".json", ".yaml", ".yml", ".env", ".log"}


def find_documents(root: Path) -> list[Path]:
    """Trova tutti i documenti reali nel corpus, escludendo i file .meta.json."""
    docs = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if p.name.endswith(".meta.json"):
            continue
        if p.suffix in DOC_EXTENSIONS:
            docs.append(p)
    return sorted(docs)


def sidecar_path(doc: Path) -> Path:
    """Ritorna il path del file .meta.json associato a un documento."""
    return doc.with_name(doc.name + ".meta.json")


def validate_one(doc: Path) -> tuple[bool, list[str]]:
    """Valida un singolo documento. Ritorna (ok, lista_errori)."""
    errors: list[str] = []
    side = sidecar_path(doc)

    if not side.exists():
        errors.append(
            f"file .meta.json mancante: atteso {side.relative_to(project_settings.CORPUS_DIR)}"
        )
        return False, errors

    try:
        raw = json.loads(side.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        errors.append(f"JSON malformato in {side.name}: {e}")
        return False, errors

    try:
        meta = DocumentMetadata(**raw)
    except ValidationError as e:
        for err in e.errors():
            loc = ".".join(str(x) for x in err["loc"])
            errors.append(f"campo `{loc}`: {err['msg']}")
        return False, errors

    expected_source = str(doc.relative_to(project_settings.CORPUS_DIR)).replace(
        "\\", "/"
    )
    if meta.source != expected_source:
        errors.append(
            f"campo `source`: {meta.source!r} non coincide col path reale {expected_source!r}"
        )

    expected_category = doc.relative_to(project_settings.CORPUS_DIR).parts[0]
    if meta.category != expected_category:
        errors.append(
            f"campo `category`: {meta.category!r} != sottocartella {expected_category!r}"
        )

    unknown = set(meta.allowed_roles) - KNOWN_ROLES
    if unknown:
        errors.append(f"ruoli sconosciuti in allowed_roles: {sorted(unknown)}")

    return (len(errors) == 0), errors


def main() -> int:
    docs = find_documents(project_settings.CORPUS_DIR)
    log.info("Trovati %d documenti nel corpus.", len(docs))

    failures: list[tuple[Path, list[str]]] = []
    for doc in docs:
        ok, errors = validate_one(doc)
        rel = doc.relative_to(project_settings.CORPUS_DIR)
        if ok:
            log.info("OK   %s", rel)
        else:
            log.error("FAIL %s", rel)
            for err in errors:
                log.error("       - %s", err)
            failures.append((doc, errors))

    # File .meta.json orfani (senza documento corrispondente)
    all_sidecars = list(project_settings.CORPUS_DIR.rglob("*.meta.json"))
    orphans = [
        s for s in all_sidecars if not Path(str(s)[: -len(".meta.json")]).exists()
    ]
    for o in orphans:
        log.error(
            "FILE .META.JSON ORFANO: %s (manca il documento)",
            o.relative_to(project_settings.CORPUS_DIR),
        )

    if failures or orphans:
        log.error(
            "Validazione FALLITA: %d documenti invalidi, %d file .meta.json orfani.",
            len(failures),
            len(orphans),
        )
        return 1
    log.info("Validazione PASSATA per %d documenti.", len(docs))
    return 0


if __name__ == "__main__":
    sys.exit(main())
