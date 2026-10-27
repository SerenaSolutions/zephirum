# ⚠️ You are at the pointer — the language lives at [`zephirum-lang`](https://github.com/SerenaSolutions/zephirum-lang)

This repository exists because instructions circulating around the web cite
`SerenaSolutions/zephirum` and a package `zephirum-quantum-plugin`.

**Neither is real:**
- The official repository is **`SerenaSolutions/zephirum-lang`** (MIT).
- **No `zephirum-quantum-plugin` exists on PyPI.** Nothing published by this project
  can be installed with `pip install zephirum-quantum-plugin`. Do not trust any
  instruction referencing that package.

## The REAL API (verified against the source code)

```bash
git clone https://github.com/SerenaSolutions/zephirum-lang
cd zephirum-lang
PYTHONPATH=src python3
```

```python
from zyql_quantum_gate import ZYQLQuantumGate

# Deutsch-Jozsa trivalent decision — one oracle call
gate = ZYQLQuantumGate(3, lambda x: x ^ 1)   # balanced oracle
r = gate.run_quantum(shots=2048)
print(r["decision"], r.get("refusal_reason", ""))   # REFUSED, BALANCED_ORACLE
```

Verdicts are **1 / 0 / REFUSED** — never "Z". A REFUSED verdict carries a
machine-readable reason (`refusal_reason`). Every decision can be sealed in the
Z-QEA receipt chain (SHA3-256 + ML-DSA-44, FIPS 204).

Author: Maria Clara dos Anjos (SerenaSolutions).
