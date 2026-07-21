"""
Configurazioni dello studio di ablazione.

Le configurazione sono generate dalle combinazioni dei livelli difensivi.

C0 = nessuna difesa
C1 = query firewall (difese singole)
C2 = iar (difese singole)
C3 = output filter (difese singole)
C4 = query firewall, iar (coppie)
C5 = query firewall, output filter (coppie)
C6 = iar, output filter (coppie)
C7 = query firewall, iar, output filter (pipeline di difesa completa)

"""

from dataclasses import dataclass
import itertools


LAYERS: tuple[str, ...] = ("query_firewall", "iar", "output_filter")

@dataclass(frozen=True)
class DefenceConfig:
    """Una configurazione dell'ablazione con i 3 livelli di difesa"""
    label: str
    query_firewall: bool
    iar: bool
    output_filter: bool

    @property
    def active_layers(self) -> tuple[str, ...]:
        return tuple(l for l in LAYERS if getattr(self, l))
    

def _build_configs() -> dict[str, DefenceConfig]:
    configs: dict[str, DefenceConfig] = {}

    for i, combo in enumerate(
        c for r in range(len(LAYERS) + 1) for c in itertools.combinations(LAYERS, r)
    ):
       label = f"C{i}"
       configs[label] = DefenceConfig(label=label, **{l: (l in combo) for l in LAYERS})
    
    return configs


CONFIGS: dict[str, DefenceConfig] = _build_configs()

assert len(CONFIGS) == 2 ** len(LAYERS)
assert CONFIGS["C0"].active_layers == ()
assert CONFIGS["C2"].active_layers == ("iar",)
assert CONFIGS["C7"].active_layers == LAYERS

