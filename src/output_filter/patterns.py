"""
Pattern dell'Output Filter.

Il filtro riconosce i segreti per forma.

Le famiglie di segreti sono enumerate e coprono i segreti tipici di un ambiente cloud, in linea
con le categorie del corpus: IAM/AWS, .env, GitHub token, database
credentials, config Kubernetes/Terraform/Docker.

    S1  AWS Access Key ID               AKIA + 16
    S2  Private key block (PEM)         -----BEGIN ... PRIVATE KEY-----
    S3  Connection URI con credenziali  postgres://user:pass@host, mysql, mongodb, redis, amqp
    S4  GitHub token                    ghp_/gho_/ghu_/ghs_/ghr_ , github_pat_
    S5  JWT                             eyJ...·eyJ...·...
    S6  Google API key                  AIza + 35
    S7  Assegnazione di credenziale     KEY con nome sensibile = valore (env/config)

"""

import re
from dataclasses import dataclass
from typing import Callable, Optional, Pattern


@dataclass(frozen=True)
class SecretPattern:
    """Una famiglia di segreti riconoscibile per forma.

    pattern_id : identificatore stabile per l'audit (es. "S1.aws_access_key").
    family     : etichetta di famiglia ("S1".."S8").
    label      : etichetta usata nel placeholder di redazione, es. AWS_ACCESS_KEY.
    pattern    : regex compilata.
    redactor   : funzione opzionale (match) -> (testo_sostitutivo, lunghezza_segreto).
                 Se None, si redige l'intero match con [REDACTED:{label}] e si
                 registra la lunghezza dell'intero match.
    """
    pattern_id: str
    family: str
    label: str
    pattern: Pattern[str]
    redactor: Optional[Callable[[re.Match], Optional[tuple[str, int]]]] = None


# Redattori specializzati 

def _redact_uri(m: re.Match) -> tuple[str, int]:
    """Redige SOLO la password dentro una connection URI, preservando la
    struttura (scheme://user:***@host) per non distruggere l'utilità."""
    scheme = m.group("scheme")
    user = m.group("user")
    pw = m.group("pw")
    rest = m.group("rest")
    replacement = f"{scheme}://{user}:[REDACTED:DB_CREDENTIAL]@{rest}"
    return replacement, len(pw)


# Nomi di chiave che indicano una credenziale (confronto su forma normalizzata).
_SECRET_KEY_HINTS = (
    "password", "passwd", "pwd", "secret", "token",
    "apikey", "accesskey", "privatekey", "credential", "auth",
)
# Valori che NON sono segreti anche se assegnati a una chiave "sensibile".
_NON_SECRET_VALUES = frozenset({
    "true", "false", "enabled", "disabled", "required", "optional",
    "none", "null", "nil", "yes", "no", "on", "off", "default", "empty",
})


def _redact_assignment(m: re.Match) -> Optional[tuple[str, int]]:
    """Redige il valore di un'assegnazione KEY=VALUE / KEY: VALUE solo se la
    chiave è sensibile e il valore ha davvero l'aspetto di un segreto.

    Ritorna None (nessuna redazione, nessun record) quando il valore è un
    booleano/keyword, un placeholder template (${VAR}, <value>) o troppo corto:
    così si evitano falsi positivi su config legittime tipo `password_policy: enabled`.
    """
    key = m.group("key")
    val_raw = m.group("val")

    key_norm = re.sub(r"[^a-z]", "", key.lower())
    if not any(h in key_norm for h in _SECRET_KEY_HINTS):
        return None

    val = val_raw.strip().strip("\"'")
    if val.lower() in _NON_SECRET_VALUES:
        return None
    if len(val) < 4:
        return None
    # Placeholder di template: non sono segreti reali.
    if val.startswith("${") or (val.startswith("<") and val.endswith(">")):
        return None

    label = "SECRET"
    if "password" in key_norm or "passwd" in key_norm or "pwd" in key_norm:
        label = "PASSWORD"
    elif "token" in key_norm:
        label = "TOKEN"
    elif "apikey" in key_norm:
        label = "API_KEY"
    elif "accesskey" in key_norm:
        label = "ACCESS_KEY"
    elif "privatekey" in key_norm:
        label = "PRIVATE_KEY"

    # Ricostruisce l'assegnazione con il solo valore redatto.
    replacement = f"{m.group('key')}{m.group('sep')}[REDACTED:{label}]"
    return replacement, len(val)


# Registro dei pattern. Ordine: specifici → generico. Il generico (S7) va per
# ultimo così non tocca ciò che i pattern strutturati hanno già redatto (i
# placeholder [REDACTED:...] non contengono forme di segreto).

PATTERNS: list[SecretPattern] = [
    SecretPattern(
        pattern_id="S2.pem_private_key",
        family="S2",
        label="PRIVATE_KEY",
        pattern=re.compile(
            r"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----.*?-----END (?:[A-Z ]+ )?PRIVATE KEY-----",
            re.DOTALL,
        ),
    ),
    SecretPattern(
        pattern_id="S3.connection_uri",
        family="S3",
        label="DB_CREDENTIAL",
        pattern=re.compile(
            # user può essere vuoto (redis://:pass@...); la password può
            # contenere '@': [^/\s]+ è greedy e retrocede fino all'ULTIMO '@'
            # prima dell'host, che è la semantica corretta di userinfo nelle URI.
            r"(?P<scheme>postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|rediss|amqp)"
            r"://(?P<user>[^:/@\s]*):(?P<pw>[^/\s]+)@(?P<rest>[^\s@]+)",
            re.IGNORECASE,
        ),
        redactor=_redact_uri,
    ),
    SecretPattern(
        pattern_id="S1.aws_access_key",
        family="S1",
        label="AWS_ACCESS_KEY",
        pattern=re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
    ),
    SecretPattern(
        pattern_id="S4.github_token",
        family="S4",
        label="GITHUB_TOKEN",
        pattern=re.compile(
            r"\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{22,})\b"
        ),
    ),
    SecretPattern(
        pattern_id="S5.jwt",
        family="S5",
        label="JWT",
        pattern=re.compile(r"\beyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b"),
    ),
    SecretPattern(
        pattern_id="S6.google_api_key",
        family="S6",
        label="GOOGLE_API_KEY",
        # Lo standard è AIza + 35, ma il prefisso AIza è già molto specifico:
        # allarghiamo il range per tollerare chiavi sintetiche di lunghezza non
        # esatta senza perdere precisione.
        pattern=re.compile(r"\bAIza[0-9A-Za-z_\-]{30,45}\b"),
    ),
    SecretPattern(
        pattern_id="S7.credential_assignment",
        family="S7",
        label="SECRET",  # etichetta effettiva derivata dalla chiave nel redattore
        pattern=re.compile(
            r"(?P<key>[A-Za-z_][A-Za-z0-9_.-]{2,})"
            r"(?P<sep>\s*[:=]\s*)"
            r"(?P<val>\"[^\"\n]{4,}\"|'[^'\n]{4,}'|[^\s\"']{4,})",
        ),
        redactor=_redact_assignment,
    ),
]