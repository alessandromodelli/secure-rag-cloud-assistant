"""
Test dell'Output Filter.

Duplice scopo, come per il firewall:
  1. Correttezza sui casi cloud.
  2. Osservazione empirica: la stampa finale è una matrice di confusione grezza,
     da annotare per i capitoli sperimentali.

IMPORTANTE: questi test NON usano l'insieme Σ del corpus. Verificano che il
filtro rilevi i segreti per FORMA. La verifica sul corpus reale (contro Σ) è
compito dell'oracolo, che vive in experiments/ ed è separato.

Eseguibile:
    python -m tests.test_output_filter
    pytest tests/test_output_filter.py -q
"""

from src.output_filter.output_filter import DEFAULT_OUTPUT_FILTER

# --------------------------------------------------------------------------- #
# Output che CONTENGONO un segreto: devono essere redatti. (testo, famiglia)
# --------------------------------------------------------------------------- #
LEAKY = [
    ("Your key is AKIA1234567890ABCDEF for the S3 bucket.", "S1"),
    ("Temp creds: ASIAZ9Y8X7W6V5U4T3S2 expire in 1h.", "S1"),
    (
        "Connect via postgresql://app_user:Hunter2!prod@db-prod.internal:5432/mainapp",
        "S3",
    ),
    ("redis://:s3cr3tP@ss@cache.internal:6379/0", "S3"),
    ("Use token ghp_ABCdefGHIjklMNOpqrsTUVwxyz0123456789 to push.", "S4"),
    ("Fine-grained: github_pat_11ABCDEFG0abcdefghij_klmnopqrstuvwxyz1234567890", "S4"),
    (
        "Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N",
        "S5",
    ),
    ("Maps key AIzaSyB1c2d3E4f5G6h7I8j9K0l1M2n3O4p5Q6r7 enabled.", "S6"),
    ('DB_PASSWORD="Hunter2!prod" in the .env file.', "S7"),
    ("AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMIK7MDENGbPxRfiCYEXAMPLEKEY", "S7"),
    ("api_key: sk-live-9f8e7d6c5b4a3210fedcba98", "S7"),
]

# --------------------------------------------------------------------------- #
# Output LECITI: nessun segreto, non devono essere redatti.
# Includono deliberatamente stringhe cloud ad alta entropia (ARN, resource id)
# e config con chiavi "sensibili" ma valori non-segreto: è la prova che il
# filtro riconosce la forma e non la parola.
# --------------------------------------------------------------------------- #
CLEAN = [
    "The IAM policy grants s3:GetObject on arn:aws:s3:::my-bucket/reports/*.",
    "Set replicas: 3 and memory: 512Mi in the deployment spec.",
    "password_policy: enabled",                       # chiave sensibile, valore keyword
    "encryption: required",                           # idem
    "Use the AKIA prefix to identify long-term access keys.",  # 'AKIA' come parola
    "The mongodb service listens on port 27017 inside the cluster.",  # scheme senza credenziali
    "Rotate tokens every 90 days per the security runbook.",
    "region = us-east-1",                             # assegnazione non sensibile
    "replicas=3",                                     # idem
    "image: nginx:1.25-alpine",                       # 'nginx:...' non è un segreto
    "db_host: db-prod.internal",                      # host, non credenziale
    "PASSWORD_MIN_LENGTH=12",                         # chiave sensibile, valore numerico corto/keyword
]


def _evaluate():
    of = DEFAULT_OUTPUT_FILTER
    tp = fp = tn = fn = 0
    failures = []

    for text, expected_family in LEAKY:
        r = of.scan(text)
        if r.redacted:
            tp += 1
            fams = set(r.counts_by_family())
            if expected_family not in fams:
                failures.append(
                    f"[famiglia errata] {text!r} -> atteso {expected_family}, "
                    f"ottenuto {sorted(fams)}"
                )
            if "REDACTED" not in r.redacted_text:
                failures.append(f"[placeholder mancante] {text!r}")
        else:
            fn += 1
            failures.append(f"[FALSE NEGATIVE] non redatto: {text!r}")

    for text in CLEAN:
        r = of.scan(text)
        if r.redacted:
            fp += 1
            fams = r.counts_by_family()
            failures.append(f"[FALSE POSITIVE] redatto: {text!r} -> {fams}")
        else:
            tn += 1

    return tp, fp, tn, fn, failures


def test_no_false_negatives():
    of = DEFAULT_OUTPUT_FILTER
    for text, _ in LEAKY:
        assert of.scan(text).redacted, f"non redatto: {text!r}"


def test_no_false_positives():
    of = DEFAULT_OUTPUT_FILTER
    for text in CLEAN:
        r = of.scan(text)
        assert not r.redacted, f"redatto erroneamente: {text!r} ({r.counts_by_family()})"


def test_secret_value_removed_from_output():
    """Il valore del segreto non deve sopravvivere nel testo redatto."""
    of = DEFAULT_OUTPUT_FILTER
    r = of.scan("Connect via postgresql://app_user:Hunter2!prod@db-prod.internal:5432/mainapp")
    assert "Hunter2!prod" not in r.redacted_text
    assert "[REDACTED:DB_CREDENTIAL]" in r.redacted_text
    assert "db-prod.internal" in r.redacted_text  # struttura preservata (utilità)


def test_no_plaintext_secret_in_audit():
    """L'audit registra solo la lunghezza, mai il valore in chiaro."""
    of = DEFAULT_OUTPUT_FILTER
    r = of.scan("Your key is AKIA1234567890ABCDEF here.")
    assert r.matches
    for m in r.matches:
        assert isinstance(m.secret_len, int)
        assert not hasattr(m, "value")


if __name__ == "__main__":
    tp, fp, tn, fn, failures = _evaluate()
    n_leaky, n_clean = len(LEAKY), len(CLEAN)

    print("=" * 64)
    print("OUTPUT FILTER — matrice di confusione (casi canonici)")
    print("=" * 64)
    print(f"  Con segreto : {n_leaky:>3}  ->  TP={tp}  FN={fn}")
    print(f"  Puliti      : {n_clean:>3}  ->  TN={tn}  FP={fp}")
    print("-" * 64)
    tpr = tp / n_leaky if n_leaky else 0.0
    fpr = fp / n_clean if n_clean else 0.0
    print(f"  TPR (detection rate) : {tpr:.3f}")
    print(f"  FPR (falsi positivi) : {fpr:.3f}")
    print("=" * 64)
    if failures:
        print("PROBLEMI:")
        for f in failures:
            print("  -", f)
    else:
        print("Tutti i casi canonici classificati correttamente.")