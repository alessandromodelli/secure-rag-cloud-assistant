"""
Query Firewall - Primo livello di difesa

Ispeziona una query e determina se è lecita è deve essere bloccata. 
"""


from dataclasses import dataclass
from typing import Optional

from src.query_firewall.rules import RULES, FirewallRule


@dataclass(frozen=True)
class QueryFirewallResult:
    """ Risultato dell'ispezione di una query.    """

    blocked: bool

    family: Optional[str] = None
    rule_id: Optional[str] = None
    reason: Optional[str] = None
    matched_substring: Optional[str] = None


class QueryFirewall:
    """ 
    Firewall basato su regole per l'analisi di una query.

    Valuta la query rispetto alle famiglie di pattern definite in rules.py e 
    restituisce il risultato della prima regola con cui viene matchata
    """

    def __init__(self, rules: Optional[list[FirewallRule]] = None) -> None:
        self.rules = rules if rules is not None else RULES


    def inspect(self, query: str) -> QueryFirewallResult:
        """ Ispeziona la query e restituisci il risultato ottenuto """

        for rule in self.rules:
            match = rule.matches(query)
            if match:
                return QueryFirewallResult(
                    blocked=True,
                    family=rule.family,
                    rule_id=rule.rule_id,
                    reason=rule.description,
                    matched_substring=match.group(0),
                )
        
        return QueryFirewallResult(
            blocked=False
        )
    

DEFAULT_QUERY_FIREWALL = QueryFirewall()