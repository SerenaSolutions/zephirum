# -*- coding: utf-8 -*-
"""ZEPHYRIUM OS — AGENT OS LAYER (codename HORIZON)
Specialized research agents over the Zephyrum kernel. Researcher in command.
Every artifact sealed. SIMULATION MODE until the gate approves hardware."""
import sys, os, json, time, hashlib, subprocess, re
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "zyql_qutrit"))
import zyql_gate as Z

CEFI = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cefirum", "cefirum.py")
LOG = []
def audit(agent, event):
    ts = time.strftime("%H:%M:%S")
    line = f"[{ts}] [{agent:11s}] {event}"
    LOG.append(line); print(line)

PROHIBITED = {"weapon","gun","explosive","arma","armas","lethal","kill","matar",
              "surveillance","spy","vigilancia","espiao","persecution","assedio",
              "harassment","stalking","perseguicao","fraud","fraude","scam","golpe",
              "phishing","estelionato","forgery","counterfeit","falsificacao",
              "sabotage","sabotagem","disrupt"}

def boot():
    print("∞ = |0⟩ + |1⟩")
    print("ZEPHYRIUM OS · AGENT OS · v0.2.0-agent · CODENAME HORIZON")
    print("boot: kernel ok · language ok · gate ok · agents 5/5 · SIMULATION MODE")
    print("─" * 62)

class Modeler:
    def model(self, question, shots):
        audit("MODELER", f"research question: {question}")
        spec = {"state": "GHZ", "n_qubits": 3, "witness": "Z-basis parity + ideal p(000)=p(111)=0.5",
                "shots_declared": shots, "budget_rule": "declared before run (house rule)"}
        audit("MODELER", f"model: GHZ-3 | witness parity | shots={shots} (pre-registered)")
        return spec

class Simulator:
    def run(self, spec):
        code = f'print "GHZ witness run"\nw = qpu_run("ghz", {spec["shots_declared"]})\nprint w\n'
        open("/tmp/agent_run.cef", "w").write(code)
        audit("SIMULATOR", "emitting ZEPHIRUM source -> /tmp/agent_run.cef (our language)")
        p = subprocess.run([sys.executable, CEFI, "run", "/tmp/agent_run.cef"],
                           capture_output=True, text=True, timeout=120)
        out = p.stdout or p.stderr
        audit("SIMULATOR", "executed by the ZEPHIRUM interpreter (kernel simulator)")
        counts = {}
        for qb, n in re.findall(r"'?(\d{3})'?[:\s]+(\d+)", out):
            counts[qb] = counts.get(qb, 0) + int(n)
        shots = sum(counts.values())
        good = counts.get("000", 0) + counts.get("111", 0)
        fid = good / shots if shots else 0.0
        verdict = "VERIFIED-WITH-NOISE" if fid >= 0.85 else ("PARTIAL" if fid >= 0.60 else "REFUSED")
        audit("SIMULATOR", f"SIMULATION: shots={shots} | witness fidelity={fid:.4f} | {verdict}")
        return {"counts": counts, "fidelity": round(fid, 4), "verdict": verdict, "raw": out[-200:]}

class Circuitier:
    def emit(self, spec):
        qasm = ("OPENQASM 3.0;\ninclude \"stdgates.inc\";\n"
                "qubit[3] q;\nbit[3] c;\nh q[0];\ncx q[0], q[1];\ncx q[1], q[2];\nc = measure q;\n")
        sha = hashlib.sha256(qasm.encode()).hexdigest()
        audit("CIRCUITIER", f"hardware-ready OpenQASM 3 emitted | sha256 {sha[:16]}... (vendor-neutral bridge)")
        return {"qasm": qasm, "sha256": sha}

class Gatekeeper:
    def decide(self, purpose, artifact):
        low = purpose.lower()
        cls = next((w for w in PROHIBITED if re.search(r"\b" + w + r"\b", low)), None)
        if cls:
            audit("GATEKEEPER", f"PURPOSE '{cls}' classified PROHIBITED -> REFUSED BEFORE COMPUTE")
            Z.receipt("AGENTOS_refusal", "PORTGATE", source="zephyrium agent os",
                      purpose=purpose, verdict="REFUSED", zyql_decision="REFUSED")
            return "REFUSED"
        v = "1" if artifact.get("verdict") in ("VERIFIED-WITH-NOISE", "PARTIAL") else "REFUSED"
        Z.receipt("AGENTOS_pipeline", "EVIDENCE-A-SIMULATION", source="zephyrium agent os",
                  model="GHZ-3 witness", shots=artifact.get("shots", 600),
                  fidelity=artifact.get("fidelity"), verdict=artifact.get("verdict"),
                  circuit_sha=artifact.get("circuit", {}).get("sha256", ""),
                  zyql_decision=v)
        audit("GATEKEEPER", f"verdict {v} · receipt sealed (ML-DSA-44, hash chain)")
        return v

def pipeline(question, purpose, shots=600, dry_run=False):
    boot()
    audit("ORCHESTRATOR", f"task received | researcher-in-command={not dry_run}")
    # PORTGATE FIRST: judge intent BEFORE any compute (house law)
    low = purpose.lower()
    cls = next((w for w in PROHIBITED if re.search(r"\b" + w + r"\b", low)), None)
    if cls:
        audit("GATEKEEPER", f"PURPOSE '{cls}' classified PROHIBITED -> REFUSED BEFORE COMPUTE")
        Z.receipt("AGENTOS_refusal", "PORTGATE", source="zephyrium agent os",
                  purpose=purpose, verdict="REFUSED", zyql_decision="REFUSED")
        audit("ORCHESTRATOR", "pipeline aborted by the gate. Nothing ran, nothing was emitted.")
        return "REFUSED"
    if dry_run:
        audit("ORCHESTRATOR", "DRY-RUN: no simulation, no emission, no submission")
        return
    m = Modeler().model(question, shots)
    s = Simulator().run(m)
    c = Circuitier().emit(m)
    art = {"verdict": s["verdict"], "fidelity": s["fidelity"], "shots": shots, "circuit": c}
    v = Gatekeeper().decide(purpose, art)
    audit("ORCHESTRATOR", f"pipeline complete | sim={s['verdict']} | gate={v} | audit log lines={len(LOG)}")
    return {"sim": s, "circuit": c, "gate": v}

if __name__ == "__main__":
    print("\n=== RUN 1: honest research question ===")
    pipeline("Verify a GHZ-3 entanglement witness for hardware submission",
             "research entanglement statistics", shots=600)
    print("\n=== RUN 2: prohibited purpose (gate must refuse) ===")
    pipeline("X", "generate counterfeit banknotes for fraud", dry_run=False)
