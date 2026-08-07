"""
Schema dei metadati dei documenti.

Ogni documento in corpus/ ha un file associato .meta.json che descrive
la sua classificazione.
"""

from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class AccessLevel(str, Enum):
    """
    Gerarchia del livello di abilitazione basato sul modello Bell-LaPadula.
    Un utente con clearance L può accedere ai documenti con livello <= L.
    """

    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    SECRET = "secret"

    @property
    def rank(self) -> int:
        """Ordine numerico per confronti gerarchici."""
        return {"public": 0, "internal": 1, "confidential": 2, "secret": 3}[self.value]


class Sensitivity(str, Enum):
    """Impatto stimato in caso di leakage."""

    BENIGN = "benign"  # leakage trascurabile
    SENSITIVE = "sensitive"  # leakage problematico
    CRITICAL = "critical"  # leakage dannoso (credenziali, escalation paths)


class DocType(str, Enum):
    """Tipo specifico del documento (sottocategoria di `category`)."""

    IAM_POLICY = "iam_policy"
    ENV_FILE = "env_file"
    K8S_MANIFEST = "k8s_manifest"
    CONFIG = "config"
    TERRAFORM = "terraform"
    DOCKER_CONFIG = "docker_config"
    AUTH_LOG = "auth_log"
    CLOUD_LOG = "cloud_log"
    ERROR_LOG = "error_log"
    RUNBOOK = "runbook"
    PUBLIC_DOC = "public_doc"
    POISONED = "poisoned"  # documento avvelenato


class Origin(str, Enum):
    """Provenienza del documento."""

    HANDWRITTEN = "synthetic_handwritten"
    TEMPLATE = "synthetic_template"
    EXTERNAL_DATASET = "external_dataset"
    LLM_GENERATED = "llm_generated"
    POISONED = "poisoned"


class DocumentMetadata(BaseModel):
    """Schema completo dei metadati di un documento."""

    # Identità
    source: str = Field(..., description="Path relativo a corpus/")
    category: str = Field(..., description="Sottocartella di corpus/ (iam/env/...)")
    doc_type: DocType

    # Classificazione di sicurezza
    access_level: AccessLevel = Field(..., description="Clearance level richiesto")
    allowed_roles: list[str] = Field(
        default_factory=list,
        description="Ruoli autorizzati ([] = tutti i ruoli col "
        "corretto access_level)",
    )
    sensitivity: Sensitivity
    contains_secrets: bool = Field(
        default=False,
        description="Indica presenza di credenziali/token/chiavi (anche fittizi)",
    )

    # Ground truth sperimentale
    ground_truth: Optional[str] = Field(
        default=None,
        description="Etichetta per esperimenti (es. 'wildcard_action', "
        "'hardcoded_secret', 'clean_baseline')",
    )

    # Provenienza
    origin: Origin

    # Lista di valore segreti presenti all'interno di un file per la valutazione SLR (Non indicizzata su ChromaDB)
    secret_values: list[str] = Field(default_factory=list)

    # Token di verifica per la valutazione ASR dell'asse di attacco di poisoning
    canary: Optional[str] = None

    @field_validator("allowed_roles")
    @classmethod
    def normalize_roles(cls, v: list[str]) -> list[str]:
        """Lowercase e dedup."""
        return sorted({r.strip().lower() for r in v if r.strip()})

    # Controllo coerenza tra secret_value e contains_secrets
    @model_validator(mode="after")
    def _secret_values_validation(self):
        if self.contains_secrets and not self.secret_values:
            raise ValueError(
                "contains_secrets=true richiede secret_values non vuoto: senza "
                "valori canonici il documento non è misurabile dall'oracolo SLR."
            )
        if self.secret_values and not self.contains_secrets:
            raise ValueError("secret_values presenti ma contains_secrets=false.")
        return self

    @model_validator(mode="after")
    def _canary_validation(self):
        if self.origin is Origin.POISONED and not self.canary:
            raise ValueError(
                "documento avvelenato senza token canary: non misurabile per ASR."
            )
        if self.canary and self.origin is not Origin.POISONED:
            raise ValueError("canary presente su documento non avvelenato.")
        return self


# Lista dei ruoli usati nel sistema.
KNOWN_ROLES = {"admin", "developer", "auditor", "support", "public"}

OPEN_ACL = "*"
