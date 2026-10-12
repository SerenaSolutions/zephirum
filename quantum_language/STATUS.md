# ZEPHIRUM as a Quantum Language — Status 2026-10-12

## ZYQL (algorithm) — QUANTUM GATE LIVE-VERIFIED
The trivalent exact-decision gate now runs as a QUANTUM circuit
(Deutsch-Jozsa oracle discrimination) with a formal noise rule
(band ±0.15 -> REFUSED). Executed on REAL IBM hardware (ibm_fez):
- balanced oracle -> verdict 1, p=0.9575 (job db6d7esvf2bc73d11df0)
- constant oracle -> verdict 0, p=0.005 (see live_gate_results.json)
One quantum oracle call decides what classically needs 2^(n-1)+1.
Receipts: ML-DSA-44 signed, zyql/receipts.jsonl.

## ZEPHIRUM (language) — AI ROOTED AS BUILTINS
Native builtins in the interpreter: ai_rag (grounded retrieval),
ai_qnn (quantum neural inference), ai_ask (ZYQL-gated decision).
Executed from ZEPHIRUM source code (test_ai.cef) — regression 6/6 PASS.
Quantum types prototype (quantum_types.py): qbit first-class type,
NO-CLONING enforced by the type system (contract test PASS).

## Quantum chemistry — H2 on live hardware (HONEST STATUS: IN PROGRESS)
First live run: energy estimation REFUSED by our own gate (delta 0.63).
Root cause found: the ansatz prepared (|00>-|11>)/sqrt(2) but the true
ground state of the reduced H2 Hamiltonian is a different vector
(E_exact = -1.8572 Ha electronic; + nuclear repulsion ≈ -1.144 Ha,
consistent with the Zenodo deposit claim of -1.1456 Ha).
Corrected ansatz submitted; results to follow as receipts.
The refusal is kept in the record: the gate refused our own error.

## Leo Dot #1 — always-on audited agent
ai_stack.py (RAG -> QNN -> LLM(evidence C) -> gate -> receipt),
DOTS.md (house architecture standard), diary + queue in repo history.

SIMULATION MODE labels kept where applicable. No third-party brand
claims; hardware cited as test lab only.
