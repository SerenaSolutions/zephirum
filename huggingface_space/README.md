---
title: ZEPHIRUM — Quantum Language
emoji: ∞
colorFrom: indigo
colorTo: blue
sdk: gradio
sdk_version: 4.44.1
app_file: app.py
pinned: false
license: mit
short_description: The quantum language with an honesty contract (trivalent 1/0/REFUSED decisions)
---

# ZEPHIRUM — The Quantum Language

Run ZEPHIRUM programs in your browser. ZEPHIRUM is an interpreted language
(lexer → parser → tree-walk executor) with native AI builtins:

- `ai_rag` — grounded retrieval before any answer
- `ai_qnn` — quantum neural inference
- `ai_ask` — trivalent ZYQL decision (1 / 0 / REFUSED)

Every decision carries a signed receipt. The interpreter refuses what it
cannot ground: no invention, no overclaim.

SIMULATION MODE: the interpreter and its quantum primitives run in
simulation on CPU. Hardware validation receipts live in the main repository
(QUANTUM HARDWARE BRIDGE, vendor-neutral).

MIT license. Main repository: github.com/SerenaSolutions/zephirum
