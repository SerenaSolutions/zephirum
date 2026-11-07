#!/usr/bin/env python3
# ZYQL S2 — BATERIA DE CONFORMIDADE DO POLICY GATE (12 casos)
# Prova: negacao por padrao, recusa com recibo, funcao NAO executada,
# anti-replay, cadeia de auditoria, limite de tempo, e a distincao
# REFUSED (politica) x ERROR (falha tecnica).
import sys, os, json, tempfile, time, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from policy_gate import PolicyGate, sha, canon

PROG = 'programa "soma_exata" versao "1.0"\nASK:\n    question: resultado == 42\n'
PH = sha(PROG.encode())
FUTURO, PASSADO = "2030-01-01T00:00:00Z", "2020-01-01T00:00:00Z"
res = {}

def pol(**over):
    p = {"policy_version": "P1-2026-11", "default_effect": "deny",
         "valid_until": FUTURO,
         "limits": {"max_seconds": 5},
         "grants": [{"grant_id": "G-001", "program_sha256": PH,
                     "capabilities": ["compute"], "max_seconds": 5,
                     "expires_at": FUTURO, "revoked": False}]}
    for g in over.get("grants", []):
        p["grants"][0].update(g)
    if "p" in over: p.update(over["p"])
    return p

def novo(over=None):
    d = tempfile.mkdtemp()
    pp = os.path.join(d, "policy.json"); json.dump(pol(**(over or {})), open(pp, "w"))
    return PolicyGate(pp, os.path.join(d, "state"))

def req(**over):
    r = {"program_sha256": PH, "capabilities": ["compute"], "seconds": 1,
         "execution_id": "exec-" + hashlib.sha256(os.urandom(8)).hexdigest()[:12],
         "purpose": "teste de conformidade S2"}
    r.update(over); return r

def check(nome, cond, det=""):
    res[nome] = {"pass": bool(cond), "detail": det}
    print(("PASS " if cond else "FAIL ") + nome + (" | " + det if det else ""))

# C01 autorizado executa
g = novo(); r = g.execute(req(), lambda: 42)
check("C01 autorizado com recibo previo e posterior",
      r["executed"] and r["result"] == 42 and r["post"]["execution_state"] == "SUCCESS"
      and r["post"]["prev_receipt_hash"] == r["pre"]["receipt_hash"])

# C02 programa nao autorizado: funcao NAO roda
g = novo(); rodou = []
r = g.execute(req(program_sha256="0"*64), lambda: rodou.append(1) or 1)
check("C02 programa fora da politica recusado sem executar",
      (not r["executed"]) and not rodou and r["refusal"]["denial_code"] == "POLICY_PROGRAM_NOT_ALLOWED")

# C03 capacidade nao concedida
g = novo(); rodou = []
r = g.execute(req(capabilities=["compute", "qpu"]), lambda: rodou.append(1) or 1)
check("C03 capacidade nao concedida recusada", (not rodou) and r["refusal"]["denial_code"] == "CAPABILITY_NOT_GRANTED")

# C04 autorizacao expirada
g = novo({"grants": [{"expires_at": PASSADO}]})
r = g.execute(req(), lambda: 1)
check("C04 autorizacao expirada recusada", r["refusal"]["denial_code"] == "GRANT_EXPIRED")

# C05 revogada
g = novo({"grants": [{"revoked": True}]})
r = g.execute(req(), lambda: 1)
check("C05 autorizacao revogada recusada", r["refusal"]["denial_code"] == "GRANT_REVOKED")

# C06 replay do mesmo execution_id
g = novo(); r1 = req(); a = g.execute(r1, lambda: 1); b = g.execute(r1, lambda: 1)
check("C06 replay bloqueado", (not b["executed"]) and b["refusal"]["denial_code"] == "REPLAY_DETECTED")

# C07 sequencia monotona na auditoria
ok, n, msg = g.verify_chain()
seqs = [json.loads(l)["seq"] for l in open(g.audit_path) if l.strip()]
check("C07 cadeia integra e sequencia monotona", ok and seqs == sorted(seqs) and len(seqs) >= 2, f"{n} eventos")

# C08 limite de recursos
g = novo(); r = g.execute(req(seconds=10), lambda: 1)
check("C08 pedido acima do limite recusado", r["refusal"]["denial_code"] == "LIMIT_EXCEEDED")

# C09 falha tecnica durante execucao = ERROR, nao REFUSED
def lento():
    time.sleep(2.5); return 1
g = novo(); r = g.execute(req(seconds=1), lento)
check("C09 interrupcao por tempo e' ERROR (nao recusa)",
      r["executed"] and r["post"]["execution_state"] == "INTERRUPTED" and r["post"]["verdict"] == "ERROR")

# C10 adulteracao da auditoria e' detectada
g = novo(); g.execute(req(), lambda: 1)
ok1, _, _ = g.verify_chain()
linhas = open(g.audit_path).read().splitlines()
e = json.loads(linhas[0]); e["event"]["purpose"] = "adulterado"
linhas[0] = json.dumps(e, sort_keys=True); open(g.audit_path, "w").write("\n".join(linhas) + "\n")
ok2, _, motivo = g.verify_chain()
check("C10 adulteracao detectada pela cadeia", ok1 and (not ok2), motivo)

# C11 recusa fica registrada com recibo proprio
g = novo(); r = g.execute(req(program_sha256="0"*64), lambda: 1)
evs = [json.loads(l) for l in open(g.audit_path) if l.strip()]
check("C11 recusa registrada com recibo e estado NOT_EXECUTED",
      any(e["event"]["kind"] == "REFUSED" for e in evs) and r["refusal"]["execution_state"] == "NOT_EXECUTED")

# C12 veredito de recusa nunca vira ERROR nem 0
check("C12 REFUSED != ERROR e != 0",
      r["refusal"]["verdict"] == "REFUSED" and r["refusal"]["verdict"] != "ERROR")

passes = sum(1 for v in res.values() if v["pass"])
recibo = {
    "marco": "S2", "nome": "POLICY GATE — NEGACAO POR PADRAO", "kernel": "ZEPHYRUM 1.12",
    "casos": len(res), "passes": passes, "falhas": len(res) - passes,
    "resultado": res,
    "escopo_honesto": {
        "enforcement": "autorizacao e recusa antes da execucao: IMPLEMENTADO",
        "anti_replay": "execution_id + sequencia monotona: IMPLEMENTADO",
        "auditoria": "cadeia de hash verificavel: IMPLEMENTADO",
        "assinatura": "AUTENTICIDADE por chave: ESPECIFICACAO (M4) — aqui so integridade",
        "sandbox_de_so": "ESPECIFICACAO (S4) — o gate autoriza, nao isola"},
}
recibo["RECEIPT_HASH"] = hashlib.sha256(canon(recibo).encode()).hexdigest()[:32]
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "RECEIPT_S2.json"), "w").write(json.dumps(recibo, indent=1, ensure_ascii=False))
print(json.dumps({"casos": len(res), "passes": passes, "RECEIPT_HASH": recibo["RECEIPT_HASH"]}, ensure_ascii=False))
print("VEREDITO:", "PASS — S2 ATIVO" if passes == len(res) else "FAIL")
sys.exit(0 if passes == len(res) else 1)
