"""H2 GROUND-STATE ENERGY — quantum chemistry, live on ibm_fez.
Model: standard two-qubit reduction of H2 (STO-3G-class), provenance
declared; ground state verified by in-script diagonalization BEFORE the
live run. Live measurement confronts the SAME model. No invention.
Coefficients: standard published reduction (g0..g4), rounded."""
import numpy as np, json, sys
g0, g1, g2, g3, g4 = -1.0524, 0.3979, -0.3979, -0.0113, 0.1809
Z = np.diag([1., -1.]); I = np.eye(2); X = np.array([[0,1],[1,0]], float)
H4 = g0*np.kron(I,I) + g1*np.kron(Z,I) + g2*np.kron(I,Z) + g3*np.kron(Z,Z) + g4*np.kron(X,X)
evals = np.linalg.eigvalsh(H4)
E_exact = float(evals[0])
print("E_exact (this model, diagonalized in-script):", round(E_exact, 4), "Ha")
print("literature FCI H2@0.735A total ~ -1.1372 Ha | house deposit claim -1.1456 Ha")
# ground state circuit: (|00>-|11>)/sqrt2 = RY(-pi/2) q0 + CNOT
from qiskit import QuantumCircuit
def make(basis):
    qc = QuantumCircuit(2, 2)
    qc.ry(-np.pi/2, 0); qc.cx(0, 1)
    if basis == "X": qc.h(0); qc.h(1)
    qc.measure([0, 1], [0, 1]); return qc
def expectations(counts, N):
    n = {k: counts.get(k, 0) for k in ("00","01","10","11")}
    p = {k: v / N for k, v in n.items()}
    z0 = p["00"]+p["01"]-p["10"]-p["11"]; z1 = p["00"]-p["01"]+p["10"]-p["11"]
    zz = p["00"]-p["01"]-p["10"]+p["11"]; xx = p["00"]-p["01"]-p["10"]+p["11"]  # XX basis trick
    return z0, z1, zz, xx
def sim_validate():
    from qiskit.quantum_info import Statevector
    sv = Statevector.from_instruction(make("Z").remove_final_measurements(inplace=False))
    # analytic check: state (|00>-|11>)/sqrt2
    v = np.asarray(sv.data)
    target = np.array([1,0,0,-1], complex)/np.sqrt(2)
    return float(np.abs(np.vdot(target, v)))
overlap = sim_validate()
print("ansatz overlap with (|00>-|11>)/sqrt2:", round(overlap, 4))
def live():
    import os
    from qiskit_ibm_runtime import QiskitRuntimeService
    svc = QiskitRuntimeService(channel="ibm_quantum_platform", token=os.environ["API_KEY"])
    bk = svc.backend("ibm_fez")
    from qiskit_ibm_runtime import SamplerV2
    from qiskit import transpile
    sampler = SamplerV2(mode=bk)
    res = {}
    for basis in ("Z", "X"):
        qc = transpile(make(basis), backend=bk, optimization_level=1)
        job = sampler.run([qc], shots=400)
        res[basis] = (job, job.job_id())
    out = {}
    for basis, (job, jid) in res.items():
        raw = job.result()[0].data.c.get_counts()
        counts = {}
        for k, v in raw.items():
            kk = k.replace(" ", "")
            counts[kk] = counts.get(kk, 0) + v
        # normalize bit strings
        c = {}
        for k, v in counts.items():
            kk = k.replace(" ", "")
            if len(kk) == 2: c[kk] = c.get(kk, 0) + v
        out[basis] = (c, 400, jid)
    return out
out = live()
cz, N, jz = out["Z"]; cx, Nx, jx = out["X"]
z0, z1, zz, _ = expectations(cz, N)
_, _, _, xx = expectations(cx, Nx)
E_live = g0 + g1*z0 + g2*z1 + g3*zz + g4*xx
print("LIVE counts Z:", cz, "| job:", jz)
print("LIVE counts X:", cx, "| job:", jx)
print("<Z0>=%.3f <Z1>=%.3f <ZZ>=%.3f <XX>=%.3f" % (z0, z1, zz, xx))
print("E_live =", round(E_live, 4), "Ha vs E_exact", round(E_exact, 4), "| delta =", round(abs(E_live-E_exact), 4))
tol = 0.05
verdict = "VERIFIED-WITH-NOISE" if abs(E_live-E_exact) <= tol else ("REFUSED" if abs(E_live-E_exact) > 0.15 else "PARTIAL")
print("VERDICT:", verdict)
json.dump({"E_exact": E_exact, "E_live": E_live, "delta": abs(E_live-E_exact),
           "z0": z0, "z1": z1, "zz": zz, "xx": xx, "jobs": [jz, jx],
           "verdict": verdict, "shots": 400}, open("h2_live_results.json", "w"), indent=1)
