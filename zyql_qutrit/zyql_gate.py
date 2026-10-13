"""ZYQL trivalent gate on qutrits + ML-DSA-44 signed receipts.

ZYQL decision map (fixed, documented):
    trit |0> -> decision "0"
    trit |1> -> decision "1"
    trit |2> -> decision "REFUSED"

Every test produces a canonical receipt signed with ML-DSA-44 (FIPS 204)
via pqcrypto. The private key never leaves this machine; receipts carry
the public key so anyone can verify.
"""
import base64, datetime, hashlib, json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
KEYDIR = os.path.join(HERE, "pq_keys")
LEDGER = os.path.join(HERE, "receipts.jsonl")
ALG = "ML-DSA-44"

from pqcrypto.sign import ml_dsa_44

DECISION = {0: "0", 1: "1", 2: "REFUSED"}

def utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def canonical(payload):
    return json.dumps(payload, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")

def _b64(b): return base64.b64encode(b).decode()
def _unb64(s): base64.b64decode(s)

def ensure_keys():
    os.makedirs(KEYDIR, exist_ok=True)
    pub_p = os.path.join(KEYDIR, "public.b64")
    priv_p = os.path.join(KEYDIR, "private.b64")
    if not (os.path.exists(pub_p) and os.path.exists(priv_p)):
        pub, priv = ml_dsa_44.keygen()
        open(pub_p, "w").write(_b64(pub))
        open(priv_p, "w").write(_b64(priv))
    return _b64_or_file(pub_p), _b64_or_file(priv_p)

def _b64_or_file(p):
    return open(p).read()

def load_pub():
    return base64.b64decode(_b64_or_file(os.path.join(KEYDIR, "public.b64")))

def load_priv():
    return base64.b64decode(_b64_or_file(os.path.join(KEYDIR, "private.b64")))

def sign(payload):
    ensure_keys()
    body = canonical(payload)
    sig = ml_dsa_44.sign(load_priv(), body)
    return _b64(sig)

def verify(payload, sig_b64):
    """Returns True if the receipt signature verifies."""
    try:
        ml_dsa_44.verify(load_pub(), canonical(payload), base64.b64decode(sig_b64))
        return True
    except Exception:
        return False

def receipt(test, evidence, **kw):
    """Build a signed receipt and append it to the ledger."""
    payload = {"alg": ALG, "evidence": evidence, "suite": "ZYQL-QUTRIT",
               "test": test, "timestamp_utc": utc()}
    payload.update(kw)
    payload["sha3_256"] = hashlib.sha3_256(canonical(payload)).hexdigest()
    sig = sign(payload)
    entry = {"payload": payload, "signature_b64": sig,
             "public_key_b64": _b64_or_file(os.path.join(KEYDIR, "public.b64"))}
    with open(LEDGER, "a") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")
    ok = verify(payload, sig)
    return entry, ok

def zyql_decide(trits):
    """Map trit outcomes to ZYQL decisions."""
    return [DECISION[int(t)] for t in trits]

def chi2_uniform(counts):
    n = np.asarray(counts, dtype=float)
    exp = n.sum() / len(n)
    return float(((n - exp) ** 2 / exp).sum())


# ==== NATIVE AI PIPELINE (rooted Oct 12, 2026, owner order) ====
# pergunta -> RAG grounding -> QNN path -> LLM consult (evidence C) -> gate -> recibo
import re
def decide_with_ai(question, llm_callable=None):
    """ZYQL gate with the AI stack rooted IN the algorithm.
    RAG grounds (evidence B corpus); LLM is evidence C and never trusted raw;
    the trivalent verdict + receipt are still the final word."""
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "kernel_intelligence"))
    import rag, qnn_fast
    hits = rag.retrieve(question, k=3)
    toks = set(re.findall(r"\w{3,}", question.lower()))
    grounded = sum(1 for h in hits if len(toks & set(re.findall(r"\w{3,}", str(h).lower()))) >= 2) if hits else 0
    if grounded == 0 and llm_callable is None:
        return Zreceiptless_refusal(question) if False else _refuse_no_evidence(question, grounded)
    if llm_callable is not None:
        raw = llm_callable(question)
        verdict = "1" if any(h[:40] in raw or raw[:40] in h for h in hits) or grounded else "REFUSED"
        return {"verdict": verdict, "grounded_chunks": grounded,
                "llm_evidence": "C", "answer_head": raw[:80]}
    return {"verdict": "1", "grounded_chunks": grounded,
            "note": "grounded in corpus; no LLM consulted (offline mode)"}

def _refuse_no_evidence(question, grounded):
    return {"verdict": "REFUSED", "grounded_chunks": grounded,
            "rule": "no corpus grounding and no LLM -> exact refusal, no invention"}
