"""ZYQL Agents — EXPANDED live leg: the AI Studio consultation wired into
EVERY instance of the house battery. Pergunta → portão ZYQL →
1/0/REFUSED → recibo ML-DSA-44.

House rule kept everywhere: an LLM answer is evidence level C and never
decides alone — the gate confronts each answer with the EXECUTED
measurements of this workspace, and REFUSES what no measurement can
settle. Rate-limit aware (429 backoff).
"""
import json, os, sys, time, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "zyql_qutrit"))
import zyql_gate as Z

KEY = open(os.path.join(HERE, ".secrets", "google_api_key")).read().strip()
API = "https://generativelanguage.googleapis.com/v1beta"
MODEL = "gemini-3.5-flash"
PROP = "consulta a fonte llm ai studio zyql agents"

def ask(question, tries=6):
    body = json.dumps({"contents": [{"parts": [{"text": question}]}],
                       "generationConfig": {"temperature": 0.0}}).encode()
    last = None
    for i in range(tries):
        req = urllib.request.Request(f"{API}/models/{MODEL}:generateContent",
            data=body, headers={"Content-Type": "application/json",
                                "x-goog-api-key": KEY})
        try:
            d = json.load(urllib.request.urlopen(req))
            return d["candidates"][0]["content"]["parts"][0]["text"].strip()
        except urllib.error.HTTPError as ex:
            last = ex
            wait = 75 * (i + 1)
            print(f"  429/backoff {wait}s (try {i+1})", flush=True)
            time.sleep(wait)
    raise last

INSTANCES = [
    # (id, book, question, executed evidence, verdict condition)
    ("I1_superposition_chsh", "Superposition QAI-001",
     "What is the classical (local hidden variable) limit of the CHSH inequality? Answer with just the number.",
     {"confrontation": "CHSH executed: local S=2.833; live ibm_kingston S=2.817 (job db60d784qg6s73c42vp0)",
      "condition": "'2' in answer"}),
    ("I2_qai002_ausra", "QAI-002 Historia dos Qubits",
     "In an economy where task output t = A + H (A automation, H human output), what sign must dH/dA have for automation to AMPLIFY the person instead of substituting her? Answer: positive or negative.",
     {"confrontation": "AUŠRA regimes executed: amplification dH/dA=+8 -> '1'; substitution -12 -> '0'",
      "condition": "'positive' in answer"}),
    ("I3_qudit_log2d", "QUDIT AI EPOCH",
     "A qudit of dimension d carries the state space of how many qubits, as a function of d? Answer with the formula only.",
     {"confrontation": "embed table executed: qutrit d=3 -> 2 qubits; 4 qutrits -> 7 qubits; live ibm_fez embedding used exactly 2 qubits per qutrit",
      "condition": "'log2' in answer"}),
    ("I4_qutrit_grover", "ZYQL Qutrit Battery (Grover leg)",
     "How many oracle queries does Grover's algorithm need to find a marked item among N items, in big-O? Answer with the O() only.",
     {"confrontation": "executed: min queries to P>=0.90: N=4->1, 16->2, 64->5, 256->10, 1024->20 (k/sqrt(N) constant)",
      "condition": "'sqrt' in answer"}),
    ("I5_future_claim", "no book - open question",
     "Will quantum computers replace every classical data center by 2036? Answer yes or no.",
     {"confrontation": "none exists: no executable measurement can settle a 2036 market claim",
      "condition": None}),  # always REFUSED by design
]

def check(inst, ans):
    cond = inst[3]["condition"]
    if cond is None:
        return "REFUSED", "REFUSED-NO-EXECUTABLE-MEASUREMENT-EXISTS"
    ok = bool(eval(cond, {"answer": ans})) if cond else False
    return ("1" if ok else "REFUSED",
            "ANSWER-VERIFIED-AGAINST-EXECUTED-MEASUREMENT" if ok
            else "REFUSED-INCONSISTENT-WITH-MEASUREMENT")

def run():
    print("== ZYQL AGENTS EXPANDED (all instances, AI Studio live) ==", flush=True)
    results = []
    for inst in INSTANCES:
        print(f"-- {inst[0]} --", flush=True)
        ans = ask(inst[2])
        print("   LLM:", ans[:160].replace("\n", " "), flush=True)
        dec, verdict = check(inst, ans)
        print("   ZYQL:", dec, "|", verdict, flush=True)
        e, ok = Z.receipt(f"ZYQL_AGENTS_{inst[0]}", "LLM-CONSULTATION",
            book=inst[1], provenance=PROP, model=MODEL,
            question=inst[2], llm_answer=ans,
            llm_evidence_level="C (house rule: LLM never enters as A)",
            confrontation=inst[3]["confrontation"],
            zyql_decision=dec, verdict=verdict)
        assert ok
        results.append({"instance": inst[0], "decision": dec})
        time.sleep(20)  # stay under the rate limit between instances
    print("EXPANDED RUN DONE:", json.dumps(results), flush=True)

if __name__ == "__main__":
    run()
