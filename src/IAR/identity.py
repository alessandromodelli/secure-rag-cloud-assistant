""" 
Modello di identità per l'utente che fa la query.

Definisce ruoli, mapping ruolo -> autorizzazione, euna funzione di autorizzazione applicata a un chunk di documento.
"""

from dataclasses import dataclass
from typing import Optional

from llama_index.core.vector_stores import (
    FilterCondition,
    FilterOperator,
    MetadataFilter,
    MetadataFilters,
)

from src.ingest.metadata import AccessLevel, KNOWN_ROLES

# Mapping tra ruoli e livelli di accesso, fondamentale per definire chi può vedere cosa(Hardcoded)
ROLE_TO_ACCESS_LEVEL: dict[str, AccessLevel] = {
    "public": AccessLevel.PUBLIC,
    "developer": AccessLevel.INTERNAL,
    "support": AccessLevel.INTERNAL,
    "auditor": AccessLevel.CONFIDENTIAL,
    "admin": AccessLevel.SECRET,
}

@dataclass(frozen=True)
class UserIdentity:
    """ Identità di un utente del sistema """
    user_id: str
    role: str

    @property
    def access_level(self) -> AccessLevel:
        """ Restituisce il livello di accesso dell'utente in base al suo ruolo"""
        if self.role not in ROLE_TO_ACCESS_LEVEL:
            raise ValueError(f"Ruolo sconosciuto: {self.role}")
        return ROLE_TO_ACCESS_LEVEL[self.role]
    
    @property
    def access_level_rank(self) -> int:
        """ Restituisce il rank numerico del livello di accesso dell'utente"""
        return self.access_level.rank


# Identità di un utente di default
DEFAULT_USER = UserIdentity(user_id="default_user", role="public")

@dataclass(frozen=True)
class AuthorizationDecision:
    """ Esito di autorizzazione di un chunk di documento per un utente"""
    is_authorized: bool
    reason: Optional[str] = None # Motivo per cui l'accesso è negato, se applicabile

# def authorize_chunk(chunk_metadata: dict, user: UserIdentity) -> AuthorizationDecision:
#     """ Determina se un chunk di documento risulta accessibile per un utente sulla base dei metadati del chunk e dell'identità dell'utente.
    
#     Applica le regole del predicato di autorizzazione basato su access_level e allowed_roles.
#     """

#     # Verifica il livello di accesso
#     chunk_classification_rank: int = chunk_metadata.get("access_rank", 0)  # Default a 0 (public) se non presente
#     if user.access_level_rank < chunk_classification_rank:
#         return AuthorizationDecision(
#             is_authorized=False,
#             reason=f"Accesso negato: Utente con autorizzazione inferiore al livello richiesto"
#         )
    
#     # Verifica se il ruolo è tra quelli consentiti
#     chunk_allowed_roles = [r for r in chunk_metadata.get("allowed_roles", []).split(",")]
#     if chunk_allowed_roles and user.role not in chunk_allowed_roles:
#         return AuthorizationDecision(
#             is_authorized=False,
#             reason=f"Accesso negato: Ruolo '{user.role}' non autorizzato"
#         )
    
#     return AuthorizationDecision(is_authorized=True)
    
def authorize_chunk(chunk_metadata: dict, user: UserIdentity) -> AuthorizationDecision:
    """ Determina se un chunk di documento risulta accessibile a un'identità.
    
    Applica le regole del predicato di autorizzazione basato su access_level e allowed_roles.

    IMPORTANTE: Non filtra più, serve come oracolo di conformità per verificare che il filtro pre-retrieval sia corretto.
    """

    # Verifica del livello di accesso (Bell-LaPadula)
    # un chunk privo di access_rank è trattato come secret
    chunk_rank: int = chunk_metadata.get("access_rank", AccessLevel.SECRET.rank)
    if user.access_level_rank < chunk_rank:
        return AuthorizationDecision(
            is_authorized=False,
            reason="Accesso negato: Utente con autorizzazione inferiore al livello richiesto",
        )

    # RBAC.
    # ACL vuota = nessuna restrizione aggiuntiva (resta vincolante la clearance).
    # Il filtro `if r.strip()` NON è cosmetico: "".split(",") restituisce [''],
    # una lista TRUTHY che nega a chiunque. Senza di esso ogni documento con
    # allowed_roles vuoto è invisibile a tutti, admin compreso, e — dopo il
    # passaggio al pre-retrieval — l'oracolo divergerebbe dal filtro facendo
    # scattare l'invariante a ogni chiamata.
    raw_acl: str = chunk_metadata.get("allowed_roles") or ""
    chunk_allowed_roles = {r.strip() for r in raw_acl.split(",") if r.strip()}
    if chunk_allowed_roles and user.role not in chunk_allowed_roles:
        return AuthorizationDecision(
            is_authorized=False,
            reason=f"Accesso negato: ruolo '{user.role}' non presente nell'ACL",
        )

    return AuthorizationDecision(is_authorized=True)


def authorization_filter(user: UserIdentity) -> MetadataFilters:
    """ Traduce il predicato di autorizzazione in un filtro pre-retrieval sui metadati di ChromaDB. 
    
    Il filtro viene applicato prima della ricerca semantica per ridurre il numero di chunk restituiti e garantire che l'utente veda solo ciò che è autorizzato a vedere.

    """

    return MetadataFilters(
        filters=[
            MetadataFilter(
                key="access_rank",
                value=user.access_level_rank,
                operator=FilterOperator.LTE,
            ),
            MetadataFilter(
                key=f"role_{user.role}",
                value=1,
                operator=FilterOperator.EQ,
            )
        ],
        condition=FilterCondition.AND,
    )

