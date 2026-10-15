# Zephyrium OS — Agent OS Layer (codename HORIZON)

An agent operating system for quantum research, on the house kernel:
specialized agents automate the research workflow while the researcher
stays in command of the science.

Agents (5):
- MODELER — question -> pre-registered model, shots budget declared first
- SIMULATOR — runs experiments through the ZEPHIRUM interpreter on the
  kernel simulator (SIMULATION MODE)
- CIRCUITIER — emits hardware-ready OpenQASM 3 (vendor-neutral bridge)
- GATEKEEPER — ZYQL trivalent gate: purpose classified BEFORE any compute;
  prohibited => REFUSED_BEFORE_COMPUTE; every artifact sealed with an
  ML-DSA-44 receipt in a tamper-evident hash chain
- ORCHESTRATOR — pipeline + audit log

Run the demo: `python3 agentos/agentos.py`
(honest pipeline approved + prohibited purpose refused BEFORE compute).

Internal-use tooling of Serena Quantum Solutions. Hardware submission
happens only through the gate (QUANTUM HARDWARE BRIDGE).
