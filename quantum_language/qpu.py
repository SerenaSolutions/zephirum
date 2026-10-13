# -*- coding: utf-8 -*-
"""
Zephyrum QPU — statevector simulator backend for Zephyrum OS.

Executes REAL linear algebra (numpy) on a simulated register.
This is a genuine computation of quantum mechanics mathematics,
labelled SIMULATION because no physical qubits are involved.

Backend abstraction follows the AUŠRA contract:
  QuantumBackend
      ├── Simulator          (this file — always available)
      └── ExternalProvider   (registered later; never faked)
"""

import numpy as np

SIMULATION_LABEL = "SIMULATION MODE — statevector simulator, no physical QPU"


class BackendNotRegistered(RuntimeError):
    pass


BACKEND_REGISTRY = {"simulator": None}  # name -> callable returning backend


class SimulatorBackend:
    kind = "simulator"

    def __init__(self, n_qubits):
        if not 1 <= n_qubits <= 12:
            raise ValueError("simulator supports 1..12 qubits")
        self.n = n_qubits
        # |00...0>
        self.state = np.zeros(2 ** n_qubits, dtype=complex)
        self.state[0] = 1.0
        self._shots_cache = None

    # -- single-qubit gates ------------------------------------------
    def _one_qubit(self, mat, q):
        # Kronecker: identity ⊗ mat ⊗ identity, little-endian qubit q
        op = np.array([[1.0]])
        for i in range(self.n):
            op = np.kron(op, mat if i == (self.n - 1 - q) else np.eye(2))
        self.state = op @ self.state

    def h(self, q):
        m = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)
        self._one_qubit(m, q)

    def x(self, q):
        m = np.array([[0, 1], [1, 0]], dtype=complex)
        self._one_qubit(m, q)

    def z(self, q):
        m = np.array([[1, 0], [0, -1]], dtype=complex)
        self._one_qubit(m, q)

    # -- two-qubit gate ----------------------------------------------
    def cnot(self, control, target):
        if control == target:
            raise ValueError("control == target")
        new = np.zeros_like(self.state)
        for idx in range(2 ** self.n):
            bits = [(idx >> k) & 1 for k in range(self.n)]
            if bits[control]:
                bits[target] ^= 1
            new[sum(b << k for k, b in enumerate(bits))] += self.state[idx]
        self.state = new

    # -- measurement --------------------------------------------------
    def measure(self, q, rng):
        probs = np.abs(self.state) ** 2
        p1 = sum(probs[idx] for idx in range(2 ** self.n) if (idx >> q) & 1)
        return int(rng.random() < p1)

    def sample(self, shots, rng):
        """Sample the full register `shots` times (collapses each time)."""
        probs = np.abs(self.state) ** 2
        probs = probs / probs.sum()
        outcomes = rng.choice(2 ** self.n, size=shots, p=probs)
        counts = {}
        for o in outcomes:
            key = format(o, f"0{self.n}b")
            counts[key] = counts.get(key, 0) + 1
        return counts

    def entanglement_check(self, q0, q1):
        """Mutual information proxy: correlation of Z-basis statistics is
        computed empirically by callers; here we return the statevector so
        the validation layer can compute exact concurrence-like metrics."""
        return self.state.copy()


def acquire(n_qubits, backend="simulator"):
    if backend not in BACKEND_REGISTRY:
        raise BackendNotRegistered(
            f"backend '{backend}' not registered — refusing to fake execution"
        )
    if backend == "simulator":
        return SimulatorBackend(n_qubits)
    return BACKEND_REGISTRY[backend](n_qubits)
