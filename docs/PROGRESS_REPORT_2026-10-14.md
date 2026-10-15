# ZEPHIRUM / ZYQL — Progress Report
2026-10-14 · compiled by the house supervisor · states per house standard

## 1. Security — receipt hash chain (was HIGH finding) — IMPLEMENTADO, TESTADO
Every C-core receipt now sealed with NONCE, TIMESTAMP_UTC, SEQ, PREV_HASH,
RECEIPT_HASH. New zyql_verify_receipt_chain rejects replay (non-increasing SEQ)
and reorder (broken PREV_HASH). Battery 6/6; regressions: core 100/100, bridge 5/5.

## 2. i18n portgate (language-barrier audit) — IMPLEMENTADO, TESTADO
Audit verified: Unicode identifiers and UTF-8 strings work (executed from source).
Gap found and fixed: prohibited purposes previously classified in English only;
now PT/ES words (fraude, golpe, vigilancia, assedio, sabotagem...) are refused
before compute. Multilingual battery 3/3.

## 3. Language battery — TESTADO, REPRODUZIDO_INDEPENDENTEMENTE
12/12 programs pass locally (hello, bell, selftest, kaplansky, divisor, quantum,
test_ai, ap3 + katas: cota_gate, dark_matter, periodic_table, cosmic_frontiers).
CI green on main (CI + CodeQL + Verify, all SUCCESS).

## 4. Continuous science log — IMPLEMENTADO
Daily cron (03:00 UTC) runs all batteries and archives signed JSONL to
science_log/. First automated run committed on 2026-10-15; manual dispatch available.

## 5. Release v1.2.0 — IMPLEMENTADO
Published with the language showcase video (all numbers from receipts):
github.com/SerenaSolutions/zephirum/releases/tag/v1.2.0

## 6. Hugging Face Spaces package — IMPLEMENTADO (deploy ready, awaiting token)
Self-contained Gradio demo of the interpreter with AI builtins (ai_rag, ai_qnn,
ai_ask); 7/7 programs pass from the Space tree. SIMULATION MODE labels kept,
vendor-neutral, English-only public piece.

## 7. Community / discoverability — IMPLEMENTADO
Homepage live (Pages, 200 OK), 3 on-ramp issues created (#4 portgate words,
#5 qif spec, #6 H2 mitigation), "Help us grow" section in README.

## 8. Decision Layer strategy — IMPLEMENTADO (docs registered)
docs/DECISION_LAYER.md: ZYQL is the decision layer the whole world plugs into;
no competition with languages. ZQ-GATE product (pip plugin intercepting
Qiskit/PennyLane/Cirq, verdicts 1/0/REFUSED/UNKNOWN + signed receipt),
roadmap M1-M5. Company dossier: docs/DEEPTECH_EARLY_STAGE.md, including the
declared hardware-access clause (free Open Plan research tier; no ownership,
partnership, or endorsement claimed).

## 9. QPU receipts (Oct 14 kata runs) — EXPERIMENTAL, NÃO_VERIFICADO as strong evidence
Pre-registered hash (sha 10e5f51e...), shot budget declared (400).
Collected by job_id: ibm_marrakesh ZZ=0.550 (DONE), ibm_kingston ZZ=0.410 (DONE),
ibm_fez QUEUED at collection time. Correlations below the house's historical
band (0.86-0.98) — honest label kept; re-run with error-map qubit selection
recommended before any claim. Earlier live-veri fied: quantum DJ gate
(balanced→1 p=0.958, constant→0 p=0.005), Bell ZZ 0.861 (verified at source),
bridge 98.8%. H2 chemistry: REFUSED twice by our own gate — honest refusal on record.

## 10. Absorption of external engineering (evidence-B, attribution kept) — IMPLEMENTADO
Google gemini-cli (13 skills, 93 tool files), Anthropic skills (19 skills +
agent-skills spec), OpenAI codex+Agents SDK (guardrails, approval policy,
typed handoffs). Absorbed as patterns; nothing executed blindly; honest
negatives declared (Cursor closed-source; Grok weights unusable in-sandbox).

## Open items
- PRODUTOS_COMERCIAIS.md v2 + VARREDURA_GITHUB_PATROCINIOS.md: not located in
  this workspace; awaiting delivery for M1 (PyPI) alignment.
- H2 live energy: blocked on readout mitigation (issue #6).
- HF Space: awaiting owner token to deploy.
