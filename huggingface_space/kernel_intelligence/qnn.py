#!/usr/bin/env python3
"""HOUSE INTELLIGENCE KERNEL — Quantum Neural Network layer.
SIMULATION MODE (evidence D, honesty contract).
Variational 2-qubit classifier: angle encoding + entangling CNOT layers,
parameter-shift gradients (Schuld et al. rule). Trained on XOR parity —
the problem a single qubit CANNOT solve; entanglement is required.
"""
import numpy as np

I2 = np.eye(2)
RY = lambda t: np.array([[np.cos(t/2), -np.sin(t/2)], [np.sin(t/2), np.cos(t/2)]], dtype=complex)
CNOT = np.array([[1,0,0,0],[0,1,0,0],[0,0,0,1],[0,0,1,0]], dtype=complex)

def apply_1q(state, gate, q):
    """Apply single-qubit gate to qubit q (little-endian: q0 = rightmost bit)."""
    st = state.reshape(2, -1) if q == 0 else state.reshape(-1, 2).T
    # general: reshape so axis 0 is qubit q
    n = int(np.log2(state.size))
    s = state.reshape([2]*n)                     # axis 0 = qubit n-1 (big-endian MSB first)
    axis = n - 1 - q
    r = np.tensordot(gate, s, axes=([1],[axis])) # -> shape (2, remaining axes)
    r = np.moveaxis(r, 0, axis)
    return r.reshape(-1)

def probs(state, q):
    n = int(np.log2(state.size))
    s = np.abs(state.reshape([2]*n))**2
    return s.sum(axis=n-1-q)  # index along qubit q axis: P(q=0), P(q=1)

def forward(x, theta, nlayers=2):
    """x: (x1,x2) real features; theta: 3*nlayers params [ry0,ry1,cnot-weight unused... ]"""
    state = np.zeros(4, dtype=complex); state[0] = 1
    state = apply_1q(state, RY(x[0]*np.pi), 0)   # angle encoding
    state = apply_1q(state, RY(x[1]*np.pi), 1)
    for l in range(nlayers):
        state = apply_1q(state, RY(theta[3*l]), 0)
        state = apply_1q(state, RY(theta[3*l+1]), 1)
        state = CNOT.dot(state)
        state = apply_1q(state, RY(theta[3*l+2]), 0)
    return probs(state, 0)[1]  # P(q0=1) = model output

def loss(theta, X, Y):
    return sum((forward(x, theta) - y)**2 for x, y in zip(X, Y)) / len(X)

def grad(theta, X, Y, s=np.pi/4):
    g = np.zeros_like(theta)
    for i in range(len(theta)):
        tp, tm = theta.copy(), theta.copy()
        tp[i] += s; tm[i] -= s
        g[i] = (loss(tp, X, Y) - loss(tm, X, Y)) / (2*np.sin(2*s))
    return g

def train(X, Y, nlayers=2, epochs=400, lr=0.15, seed=7):
    rng = np.random.default_rng(seed)
    theta = rng.uniform(-np.pi, np.pi, 3*nlayers)
    for e in range(epochs):
        theta -= lr * grad(theta, X, Y)
    return theta, loss(theta, X, Y)

if __name__ == "__main__":
    XOR = [([0.,0.],0.), ([0.,1.],1.), ([1.,0.],1.), ([1.,1.],0.)]
    print("=== TRAIN ON 3, TEST THE 4TH (hold-one-out generalization) ===")
    results = {}
    for hold in range(4):
        X = [x for i,(x,_) in enumerate(XOR) if i != hold]
        Y = [y for i,(_,y) in enumerate(XOR) if i != hold]
        hx, hy = XOR[hold]
        theta, l = train(X, Y)
        pred = forward(hx, theta, 2)
        ok = (pred > 0.5) == (hy == 1)
        results[hold] = ok
        print(f"hold-out x={hx} true={hy} pred={pred:.4f} -> {'OK' if ok else 'FAIL'}")
    print("HOLD-ONE-OUT:", "4/4 GENERALIZES" if all(results.values()) else f"{sum(results.values())}/4")
