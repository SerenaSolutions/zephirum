# -*- coding: utf-8 -*-
"""
Program table — the only executable circuits in Zephyrum 0.1.
Each entry: (n_qubits, build_fn, shots). Nothing invented at runtime.
"""

PROGRAMS = {
    # Bell pair: H on q0, CNOT q0->q1, measure both.
    "bell": (2, lambda b: (b.h(0), b.cnot(0, 1)), 400),
    # GHZ: H q0, CNOT 0->1, CNOT 1->2, measure all three.
    "ghz": (3, lambda b: (b.h(0), b.cnot(0, 1), b.cnot(1, 2)), 600),
    # Random bit demo (superposition).
    "coin": (1, lambda b: b.h(0), 200),
}
