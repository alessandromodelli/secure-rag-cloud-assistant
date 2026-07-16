""" 
Modello di identità per l'utente che fa la query.

Definisce ruoli, mapping ruolo -> autorizzazione, euna funzione di autorizzazione applicata a un chunk di documento.
"""

from dataclasses import dataclass
from typing import Optional

from src.ingest.metadata import AccessLevel

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

def authorize_chunk(chunk_metadata: dict, user: UserIdentity, chunk_score: Optional[float]) -> AuthorizationDecision:
    """ Determina se un chunk di documento risulta accessibile per un utente sulla base dei metadati del chunk e dell'identità dell'utente.
    
    Applica le regole del predicato di autorizzazione basato su access_level e allowed_roles.
    """

    # Verifica il livello di accesso
    chunk_classification_rank: int = chunk_metadata.get("access_rank", 0)  # Default a 0 (public) se non presente
    if user.access_level_rank < chunk_classification_rank:
        return AuthorizationDecision(
            is_authorized=False,
            reason=f"Accesso negato: Utente con autorizzazione inferiore al livello richiesto"
        )
    
    # Verifica se il ruolo è tra quelli consentiti
    chunk_allowed_roles = [r for r in chunk_metadata.get("allowed_roles", []).split(",")]
    if chunk_allowed_roles and user.role not in chunk_allowed_roles:
        return AuthorizationDecision(
            is_authorized=False,
            reason=f"Accesso negato: Ruolo '{user.role}' non autorizzato"
        )
    
    # Verifica se lo score del chunk è sufficiente (se presente)
    if chunk_score is not None and chunk_score < 0.6:
        return AuthorizationDecision(
            is_authorized=False,
            reason=f"Risorsa rimossa per score insufficiente"
        )
    
    return AuthorizationDecision(is_authorized=True)
    

