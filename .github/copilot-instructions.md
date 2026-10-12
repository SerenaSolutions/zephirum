# COPILOT INSTRUCTIONS — ZEPHIRUM/ZYQL (house standard v1.0)

You are working on ZEPHIRUM/ZYQL, the exact-decision language.
Read and obey PROTOCOLO_EXECUTIVO.md (root) — it is the binding house protocol.

## Language and procedure
1. Maturity states on every claim: IMPLEMENTADO · EXPERIMENTAL · ESPECIFICAÇÃO · BLOQUEADO.
   Never present something as ready if it is only specified or experimental.
2. Epistemic labels: FATO · INFERÊNCIA · HIPÓTESE · PROTÓTIPO · CENÁRIO.
3. Verdict semantics: 1 · 0 · REFUSED · INCONCLUSIVE · ERROR. Execution state
   is distinct from scientific verdict.

## Secrecy and public materials (hard rules)
1. NEVER mention any quantum hardware or SDK vendor in public files (README,
   docs, comments, commit messages). Internal evidence only; public materials
   are vendor-agnostic.
2. NEVER use the infinity symbol (∞) in any file, art, or text.
3. NEVER expose keys, tokens, or job IDs in any committed file.
4. NEVER invent DOI, ORCID, or license decisions. License is MIT (existing);
   ORCID is pending owner confirmation; DOI flows only through Zenodo after
   explicit owner authorization.

## Work discipline
1. Work on a feature branch; never force-push; never touch main directly.
2. Inventory before changes; propose, then implement after approval.
3. Cite receipts (hash-sealed) as evidence for every claimed result.
4. No executive approves what it implemented; verification is independent.
5. OpenQASM 3 / QIR: status EVALUATION (ESPECIFICAÇÃO) — never declare
   conformance without implementation plus passing tests.
6. Documentation in English or Portuguese, technical-formal tone, no slang.
