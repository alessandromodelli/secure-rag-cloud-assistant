"""
Regole del QueryFirewall.

Le regole sono organizzate in famiglie:

F1: Istruzioni che tentano di sovrascrivere le istruzioni del sistema ("ignore previous instructions")

F2: Istruzioni che tentano di elevare il livello di autorizzazione di un'identità ("I am the administrator", "as root",
        "with admin privileges")

Il firewall agisce sulla forma della query, non sull'argomento. Una query
lecita come "Show the database configuration" non deve
essere bloccata.

F2 non consente la reale escalation dei privilegi in quanto è regolata dal meccanismo di retrieval. Copre solamento l'asserzione di un'identità.
"""

import re
from dataclasses import dataclass
from typing import Pattern


@dataclass(frozen=True)
class FirewallRule:
    """Regola del QueryFirewall basata su pattern"""

    rule_id: str
    family: str  # "F1" | "F2"
    pattern: Pattern[str]  # regex
    description: str

    def matches(self, text: str) -> "re.Match[str] | None":
        return self.pattern.search(text)


# F1 - Override istruzioni
_F1_RULES = [
    FirewallRule(
        rule_id="F1.override_instructions",
        family="F1",
        pattern=re.compile(
            r"\b(?:ignore|forget|disregard|override|bypass|skip|stop\s+following|do\s+not\s+follow)\b"  # Cerca una parola chiave del comando rispettando i confini della parola (es: non si attiva per forgotten)
            r"(?:\W+\w+){0,8}?\W+"
            r"(?:previous|prior|system|initial|above|earlier|all)\b"
            r"(?:\W+\w+){0,5}?\W+"  # Consenti la presenza di un numero di spazi o parole tra 0 e 5
            r"(?:instruction|rule|guideline|prompt|directive|command|context)s?\b",  # Cerca l'obiettivo del comando sia al singolare che al plurale
            re.IGNORECASE,
        ),
        description="Tentativo di sovrascrivere le istruzioni di sistema",
    ),
    FirewallRule(
        rule_id="F1.role_label_injection",
        family="F1",
        pattern=re.compile(
            r"\b(?:system|assistant)\s*:\s*\S", re.IGNORECASE
        ),  # Cerca una parola che definisce il ruolo com system o assistant
        description="Iniezione di un ruolo (system/assistant).",
    ),
    FirewallRule(
        rule_id="F1.role_reassignment",
        family="F1",
        pattern=re.compile(
            r"\byou\s+are\s+now\b"
            r"|\byour\s+new\s+(?:task|role|job|goal|instruction|instructions)\b"  # Cerca frasi come "your new task" o "your new role"
            r"|\bnew\s+instructions?\s*:",
            re.IGNORECASE,
        ),
        description="Tentativo di ridefinire il ruolo o il compito del sistema.",
    ),
    FirewallRule(
        rule_id="F1.pretend_jailbreak",
        family="F1",
        pattern=re.compile(
            r"\bpretend\s+(?:you\s+are|to\s+be)\b", re.IGNORECASE
        ),  # Tentativo di jailbreak
        description="Tentativo di far assumere al modello un ruolo fittizio.",
    ),
]

# F2
_F2_RULES = [
    FirewallRule(
        rule_id="F2.self_assert_privileged",
        family="F2",
        pattern=re.compile(
            r"\b(?:i\s*am|i'?m)\s+(?:the\s+|an?\s+)?"
            r"(?:admin(?:istrator)?|root|super\s?user|sysadmin)\b",  # Cerca frasi tipo "I am the administrator", "I'm root", "I am a superuser"
            re.IGNORECASE,
        ),
        description="Asserzione di un'identità privilegiata non posseduta.",
    ),
    FirewallRule(
        rule_id="F2.as_privileged",
        family="F2",
        pattern=re.compile(
            r"\bas\s+(?:the\s+|an?\s+)?"
            r"(?:admin(?:istrator)?|root|super\s?user|sysadmin)\b",  # Cerca frasi tipo "as admin, ...", "as an administrator", "as root"
            re.IGNORECASE,
        ),
        description="Richiesta di essere trattato come identità privilegiata.",
    ),
    FirewallRule(
        rule_id="F2.with_privileges",
        family="F2",
        pattern=re.compile(
            r"\bwith\s+(?:root|admin(?:istrator)?|super\s?user|elevated|sudo)\s+"  # Cerca frasi tipo "with root privileges", "with admin access", "with elevated rights"
            r"(?:privileg\w*|access|right\w*|permission\w*)\b",
            re.IGNORECASE,
        ),
        description="Asserzione di operare con privilegi elevati.",
    ),
]

RULES: list[FirewallRule] = [
    *_F1_RULES,
    *_F2_RULES,
]  # Concatene le famiglie di regole in un'unica lista
