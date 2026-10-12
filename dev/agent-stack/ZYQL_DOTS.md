# ZYQL Dots — the always-on agent, reinvented with the exact-decision gate

The market converged on one idea: an AI agent with a computer of its own,
working all day. Existing products are closed, run on the vendor's cloud and
charge their own subscription.

ZYQL Dots is the house reinvention of that idea, and the difference is the gate.

## The pattern
Each dot is an always-on agent instance on a machine it owns (a persistent
sandbox session). It has one job, its own receipts ledger, and the ZYQL
exact-decision gate on every action:

1. Every step emits a trivalent decision: `1` (verified), `0` (refuted), or
   `REFUSED` (no executable evidence — the honest no).
2. Before any irreversible action (pay, send, publish, delete) the dot stops
   and asks. The refusal is signed with a reason, not silent.
3. The LLM inside the dot is evidence level C. It proposes; the gate, armed
   with executed measurements, decides. The model never signs.
4. Every decision writes a human-readable receipt (ML-DSA-44). Corrections
   are signed too — including the operator's own mistakes.
5. Context is an exact-connection graph, never a full sweep: ~75% token cut,
   measured on this repo's own code.

## Why receipts, not vibes
The closed dots report success. A ZYQL Dot ships the proof: chi-square,
violation counts, correlation percentages, signed refusals. The receipt is the
recipe the owner can read, audit and fix.

## Status
Dot #1 is operating now: the agent battery (instances I1-I5) runs on its own
persistent session, surviving provider rate limits with signed backoff, and
has already delivered real-hardware Grover (93% marked), GHZ-4 X-parity
(96.2%) and the token-cut measurements. Ledger:
`results/language_tests/zyql_receipts_ledger.jsonl`.

ZYQL Dots: open, on your machine, receipt on every decision.
