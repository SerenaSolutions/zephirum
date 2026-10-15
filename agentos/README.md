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

## v0.3.0 — 6th agent + real hardware route
- LEODOT: the permanent dot workforce plugged as the 6th agent (supervised process).
- BRIDGE: real hardware submission happens ONLY through a gate verdict of 1,
  with hashed pre-registration, declared shot budget and EXPERIMENTAL maturity
  label (house rules). Prohibited purpose => hardware never touched.
- Credentials via env only (QPU_API_KEY / QPU_BACKEND). Vendor-neutral bridge.
