# ZYQL — A Language with Proof Obligations

ZYQL is the native language of the Zephyrum kernel: every execution
carries a contract, produces a receipt, and never confuses a computed
fact with a hypothesis.

Milestones in this update:

1. Formal grammar ZYQL v1.0 (EBNF, ISO/IEC 14977 notation, freely cited)
   with a zero-dependency recursive descent parser, semantics 1/0/REFUSED.
   Proven over the full witness corpus: 101/101 accepted, 101/101
   canonical round-trip, 12/12 invalid programs refused, Dirac literals
   (ket/bra) implemented and proven.
2. Compiler v0.1 (ZYQL source -> quantum circuit IR) with exact rational
   arithmetic, a built-in validation harness, and retrieval over the
   language's own documentation cited in every compile receipt.
3. Exact-computation batteries, all with sealed receipts:
   QEC Steane [[7,1,3]], surface codes d=3/5/7, exact Shor, QPE of H2.
   Every battery separates EXACT arithmetic from NUMERICAL sampling and
   labels both.
4. Threat model S1 and architecture conformity matrix: deny-by-default
   policy, layered isolation, compliance states distinct from scientific
   verdicts (1 / 0 / REFUSED / INCONCLUSIVE / ERROR).
5. Public-claim test: the language verified the numeric core of a public
   post about the Planck energy (E_P = 1.2209e19 GeV) with certified
   integer interval arithmetic, and labeled the speculative parts as
   HYPOTHESIS, not fact.

Vendor-agnostic by design. No hardware provider is referenced in
public materials; quantum evidence cites no vendor.
