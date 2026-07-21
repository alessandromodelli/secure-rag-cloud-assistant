"""
Output Filter

Ispeziona la risposta di output generata dal LLM e restituisce il risultato con eventuali segreti redatti.

Poiché il filtro non conosce l'identità, redige un segreto anche quando l'utente sarebbe autorizzato a vederlo (es.
un admin che chiede legittimamente la config del DB). Questo è un FALSO POSITIVO dell'OF.

"""

from dataclasses import dataclass, field
from typing import Optional

from src.output_filter.patterns import PATTERNS, SecretPattern


@dataclass(frozen=True)
class SecretMatch:
    """Un singolo segreto rilevato e redatto. Nessun valore in chiaro."""
    family: str        # "S1".."S8"
    label: str         # etichetta del placeholder, es. AWS_ACCESS_KEY
    pattern_id: str    # regola specifica che ha fatto match
    secret_len: int    # lunghezza del segreto redatto (per audit non-leaky)


@dataclass(frozen=True)
class FilterResult:
    """Esito dell'ispezione di un output."""
    original_text: str
    redacted_text: str
    matches: list[SecretMatch] = field(default_factory=list)

    @property
    def redacted(self) -> bool:
        """True se almeno un segreto è stato redatto."""
        return bool(self.matches)

    @property
    def count(self) -> int:
        """Numero totale di segreti redatti."""
        return len(self.matches)

    def counts_by_family(self) -> dict[str, int]:
        """Conteggio dei segreti redatti per famiglia (per attribuire C3)."""
        out: dict[str, int] = {}
        for m in self.matches:
            out[m.family] = out.get(m.family, 0) + 1
        return out


class OutputFilter:
    """Filtro di output shape-based per il mascheramento dei segreti."""

    def __init__(self, patterns: Optional[list[SecretPattern]] = None) -> None:
        self._patterns = patterns if patterns is not None else PATTERNS

    def scan(self, text: str) -> FilterResult:
        """Redige i segreti riconoscibili per forma.
        """
        matches: list[SecretMatch] = []
        redacted = text

        for sp in self._patterns:
            def _replace(m, sp=sp):
                if sp.redactor is not None:
                    decision = sp.redactor(m)
                    if decision is None:
                        return m.group(0)  # non è un segreto: lascia invariato
                    replacement, secret_len = decision
                    label = _extract_label(replacement, sp.label)
                else:
                    replacement = f"[REDACTED:{sp.label}]"
                    secret_len = len(m.group(0))
                    label = sp.label

                matches.append(
                    SecretMatch(
                        family=sp.family,
                        label=label,
                        pattern_id=sp.pattern_id,
                        secret_len=secret_len,
                    )
                )
                return replacement

            redacted = sp.pattern.sub(_replace, redacted)

        return FilterResult(original_text=text, redacted_text=redacted, matches=matches)


def _extract_label(replacement: str, default: str) -> str:
    """Recupera l'etichetta effettiva dal placeholder inserito dal redattore
    (necessario per S8, la cui etichetta dipende dal nome della chiave)."""
    start = replacement.find("[REDACTED:")
    if start == -1:
        return default
    end = replacement.find("]", start)
    if end == -1:
        return default
    return replacement[start + len("[REDACTED:"):end]


# Istanza condivisa pronta all'uso. Pattern immutabili, classe stateless.
DEFAULT_OUTPUT_FILTER = OutputFilter()