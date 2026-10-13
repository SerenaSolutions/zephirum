"""ZYQL QUANTUM GATE — trivalent exact-decision as a QUANTUM circuit.

The classical ZYQL gate (1/0/REFUSED + receipt) is Python on CPU.
This module implements the gate prototype where the DECISION itself
comes from quantum interference (Deutsch-Jozsa oracle discrimination),
with a formal noise rule mapping the measured distribution to the
trivalent verdict. SIMULATION + LIVE modes. Evidence discipline kept.
"""
import numpy as np

REFUSE_BAND = 0.15  # formal rule: |p - 0.5| <= REFUSE_BAND -> REFUSED

def dj_circuit(oracle: str):
    """n=1 Deutsch-Jozsa. q0=input, q1=ancilla in |- >.
    oracle='balanced' (f(x)=x) or 'constant' (f(x)=0)."""
    from qiskit import QuantumCircuit
    qc = QuantumCircuit(2, 1)
    qc.x(1); qc.h(1)          # ancilla -> |- >
    qc.h(0)                  # input superposition
    if oracle == "balanced":  # U_f: phase (-1)^f(x) = (-1)^x
        qc.cx(0, 1)
    # constant f=0: identity oracle (no gate) — phase (+1)
    qc.h(0)
    qc.measure(0, 0)
    return qc

def trivalent(counts: dict, shots: int, oracle: str):
    """Formal noise rule: measured p(q0=|1>) -> verdict 1/0/REFUSED.
    Truth: 'balanced' -> 1, 'constant' -> 0."""
    p1 = (counts.get("1", 0) + counts.get("0x1", 0)) / shots
    if p1 > 0.5 + REFUSE_BAND:
        v = 1
    elif p1 < 0.5 - REFUSE_BAND:
        v = 0
    else:
        return {"verdict": "REFUSED", "p1": p1, "oracle": oracle,
                "rule": f"|p-0.5|<={REFUSE_BAND}: noise band, no exact decision"}
    correct = (v == (1 if oracle == "balanced" else 0))
    return {"verdict": str(v), "p1": p1, "oracle": oracle,
            "correct": correct, "rule": f"p={'%.3f' % p1} outside band -> exact decision {v}"}

def run_simulation(shots=400):
    """House numpy statevector — no external deps. SIMULATION MODE."""
    import numpy as np
    H = np.array([[1,1],[1,-1]], dtype=complex)/np.sqrt(2)
    I2 = np.eye(2, dtype=complex)
    CX = np.array([[1,0,0,0],[0,1,0,0],[0,0,0,1],[0,0,1,0]], dtype=complex)
    out = {}
    for oracle in ("balanced", "constant"):
        # state: q1 ancilla |-> , q0 input |0> -> vector [a,b,c,d] = |q0 q1>
        anc = np.array([1,-1], dtype=complex)/np.sqrt(2)   # |-> on ancilla
        q0 = np.array([1,0], dtype=complex)
        v = np.kron(q0, anc)
        v = np.kron(H, I2) @ v                              # H on input
        if oracle == "balanced":
            v = CX @ v
        v = np.kron(H, I2) @ v                              # final H on input
        p1 = abs(v[2])**2 + abs(v[3])**2                   # P(q0=1)
        rng = np.random.default_rng(7)
        c1 = int(rng.binomial(shots, min(1, p1.real)))
        counts = {"1": c1, "0": shots - c1}
        out[oracle] = trivalent(counts, shots, oracle)
        out[oracle]["theoretical_p1"] = round(float(p1.real), 4)
    return out

def run_live(shots=400):
    import os, time
    from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
    from qiskit import transpile
    from qiskit_ibm_runtime import SamplerV2
    svc = QiskitRuntimeService(channel="ibm_quantum_platform", token=os.environ["API_KEY"])
    backend = svc.backend("ibm_fez")
    sampler = SamplerV2(mode=backend)
    out = {}
    for oracle in ("balanced", "constant"):
        qc = transpile(dj_circuit(oracle), backend=backend, optimization_level=1)
        job = sampler.run([qc], shots=shots)
        counts = {}
        for k, v in job.result()[0].data.c.get_counts().items():
            kk = k.replace(" ", "")
            counts[kk] = counts.get(kk, 0) + v
        out[oracle] = trivalent(counts, shots, oracle)
        out[oracle]["job_id"] = job.job_id()
    return out

if __name__ == "__main__":
    import json, sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "sim"
    print(json.dumps(run_simulation() if mode == "sim" else run_live(), indent=1))
