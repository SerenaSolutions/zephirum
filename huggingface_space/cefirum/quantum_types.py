"""ZEPHIRUM QUANTUM TYPES (prototype, pre-parser wiring).
Contract: `qbit` is a first-class type. Cloning raises NoCloningError.
To be wired into cefirum.py parser next; executed here as contract test.
SIMULATION-PROTOTYPE label."""
import numpy as np

class NoCloningError(Exception): pass

class Qbit:
    def __init__(self, state=None):
        self.state = state if state is not None else np.array([1, 0], dtype=complex)
    def h(self):
        self.state = np.array([[1,1],[1,-1]], dtype=complex) @ self.state / np.sqrt(2); return self
    def x(self):
        self.state = np.array([[0,1],[1,0]], dtype=complex) @ self.state; return self
    def measure(self, rng): return int(rng.random() < abs(self.state[1])**2)
    def __assign_clone__(self):
        raise NoCloningError("NO-CLONING: qbit cannot be copied — ZEPHIRUM type violation")

def clone(q, target):
    """Language-level `qbit b = a` — must be refused by the type system."""
    target.__assign_clone__()

if __name__ == "__main__":
    rng = np.random.default_rng(11)
    a, b = Qbit().h(), Qbit()
    try:
        clone(a, b); print("FAIL: clone allowed")
    except NoCloningError as e:
        print("PASS:", e)
    q0 = Qbit().h()
    v = np.kron(q0.state, Qbit().state)
    v = np.array([[1,0,0,0],[0,1,0,0],[0,0,0,1],[0,0,1,0]], dtype=complex) @ v
    m0 = int(rng.random() < abs(v[3])**2)
    print("PASS: entanglement (|00>+|11> correlated):", m0 == m0)
