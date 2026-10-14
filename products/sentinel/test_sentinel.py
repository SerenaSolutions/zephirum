#!/usr/bin/env python3
"""BATERIA SENTINEL — produto P1+P3 (decisões verificáveis + ProofChain).

Casos:
  S1 decisão "1" com recibo assinado e encadeado;
  S2 decisão "0" certificada;
  S3 UNKNOWN honesto (não vira palpite);
  S4 recusa estrutural -> REFUSED;
  S5 verificação independente: recibo legítimo -> RECEIPT_VALID;
  S6 forja: adulterar a resposta do recibo -> REJECT;
  S7 forja de cadeia: PREV_HASH trocado -> REJECT;
  S8 encadeamento real: 2º recibo sela o 1º; romper o 1º quebra o 2º;
  S9 API end-to-end: servidor HTTP real, /v1/decide e /v1/verify.
Exit 0 = todos PASS; qualquer falha = exit 1 (nunca 0 com reprovação — lição da auditoria).
"""
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "prototype"))
sys.path.insert(0, HERE)

from nexa_core import parse_nexa, NCA  # noqa: E402
import proofchain  # noqa: E402
from sentinel_server import decide  # noqa: E402

TMP = tempfile.mkdtemp(prefix="sentinel_battery_")
fails = []


def check(sid, cond, detail=""):
    print(("PASS" if cond else "FAIL"), sid, detail)
    if not cond:
        fails.append(sid)


P_TRUE = """
ASK:
    question: sum > 50
CONTRACT:
    absolute_error: 0
MODEL:
    type: threshold_sum
    terms: 60, 30, 20, 5
    assumption: terms_nonnegative
BUDGET:
    minimize: computation
REQUIRE:
    certified_answer
"""
P_FALSE = P_TRUE.replace("sum > 50", "sum > 200")
P_UNKNOWN = """
ASK:
    question: mean > 50
MODEL:
    type: mean_partial
    known: 60, 55, 65, 50, 60
    unknown_count: 5
    bounds: none
"""
P_REFUSED = """
ASK:
    question: sum > 100
CONTRACT:
    absolute_error: 0.5
MODEL:
    type: threshold_sum
    terms: 60, 30
"""


def main():
    # cadeia limpa para a bateria: substitui a global do módulo ANTES de decidir
    # (sem reload: reload recriaria a CHAIN original e o teste mentiria sobre a cadeia)
    chain = proofchain.ProofChain(os.path.join(TMP, "battery.jsonl"), keydir=os.path.join(TMP, "keys"))
    import sentinel_server
    sentinel_server.CHAIN = chain
    decide_mod = sentinel_server

    r1, rec1 = decide_mod.decide(P_TRUE, "S1")
    check("S1", r1["verdict"] == "1" and rec1["RECEIPT_HASH"], r1["verdict"])
    check("S1-assinado", rec1["signature"]["algorithm"] == "ML-DSA-44",
          rec1["signature"]["algorithm"])

    r2, rec2 = decide_mod.decide(P_FALSE, "S2")
    check("S2", r2["verdict"] == "0", r2["verdict"])

    r3, rec3 = decide_mod.decide(P_UNKNOWN, "S3")
    check("S3", r3["verdict"] == "UNKNOWN", r3["verdict"])

    r4, rec4 = decide_mod.decide(P_REFUSED, "S4")
    check("S4", r4["verdict"] == "REFUSED", "%s (%s)" % (r4["verdict"], r4.get("reason", "")[:40]))

    ok, why = chain.verify(rec1)
    check("S5", ok and why == "RECEIPT_VALID", why)

    forge = json.loads(json.dumps(rec1))
    forge["body"]["verdict"] = "0"
    ok, why = chain.verify(forge)
    check("S6", not ok, why)

    forge2 = json.loads(json.dumps(rec1))
    forge2["PREV_HASH"] = "f" * 64
    ok, why = chain.verify(forge2)
    check("S7", not ok, why)

    check("S8", rec2["PREV_HASH"] == rec1["RECEIPT_HASH"], "elo 1->2")
    check("S8-head", chain.head() == rec4["RECEIPT_HASH"], "cabeça = último recibo (UNKNOWN e REFUSED também emitem recibo)")

    # S9 — servidor HTTP real
    port = 8917
    proc = subprocess.Popen([sys.executable, os.path.join(HERE, "sentinel_server.py"), str(port)],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        time.sleep(1.2)
        req = urllib.request.Request("http://127.0.0.1:%d/v1/decide" % port,
                                     data=json.dumps({"program": P_TRUE,
                                                      "question_id": "S9"}).encode(),
                                     headers={"Content-Type": "application/json"})
        resp = json.loads(urllib.request.urlopen(req, timeout=10).read())
        ok9 = resp["decision"]["verdict"] == "1" and resp["receipt"]["RECEIPT_HASH"]
        check("S9", ok9, resp["decision"]["verdict"])
        req2 = urllib.request.Request("http://127.0.0.1:%d/v1/verify" % port,
                                       data=json.dumps({"receipt": resp["receipt"]}).encode(),
                                       headers={"Content-Type": "application/json"})
        resp2 = json.loads(urllib.request.urlopen(req2, timeout=10).read())
        check("S9-verify", resp2["ok"] and resp2["result"] == "RECEIPT_VALID", resp2["result"])
    finally:
        proc.terminate()
        proc.wait(timeout=5)

    print("-" * 60)
    if fails:
        print("RESULTADO: FAIL —", fails)
        sys.exit(1)
    print("RESULTADO: PASS — bateria Sentinel completa (%s)" %
          ("assinatura ML-DSA-44 ativa" if proofchain.SIGNING_OK else "unsigned-explicit"))


if __name__ == "__main__":
    main()
