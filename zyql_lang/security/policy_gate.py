#!/usr/bin/env python3
# ZYQL S2 — POLICY GATE (negacao por padrao) — kernel ZEPHYRUM 1.12
# Escopo HONESTO deste marco:
#   ENFORCEMENT REAL: autorizacao antes da execucao, recusa com recibo,
#   anti-replay, cadeia de auditoria, limites declarados e interrupcao.
#   NAO e sandbox de SO (S4) e NAO assina com chave (M4/autenticidade):
#   aqui ha INTEGRIDADE (hash), nao AUTENTICIDADE. Distincao da casa.
import json, hashlib, os, time, uuid, signal

class Denied(Exception):
    def __init__(self, code, detail=""):
        self.code = code; self.detail = detail
        super().__init__(f"{code}: {detail}")

def sha(b): return hashlib.sha256(b).hexdigest()
def canon(o): return json.dumps(o, sort_keys=True, separators=(",", ":"))

class PolicyGate:
    def __init__(self, policy_path, state_dir):
        with open(policy_path) as f: self.policy = json.load(f)
        self.state_dir = state_dir; os.makedirs(state_dir, exist_ok=True)
        self.audit_path = os.path.join(state_dir, "audit.jsonl")
        self.seq_path = os.path.join(state_dir, "seq.json")
        self.seen_path = os.path.join(state_dir, "seen_ids.json")
        self.seen = json.load(open(self.seen_path)) if os.path.exists(self.seen_path) else []
        self.seq = json.load(open(self.seq_path))["last"] if os.path.exists(self.seq_path) else 0

    # ---------- cadeia de auditoria ----------
    def _last_hash(self):
        if not os.path.exists(self.audit_path): return "GENESIS"
        last = None
        for ln in open(self.audit_path):
            if ln.strip(): last = ln
        return json.loads(last)["entry_hash"] if last else "GENESIS"

    def _audit(self, event):
        prev = self._last_hash()
        self.seq += 1
        entry = {"seq": self.seq, "ts": round(time.time(), 6), "prev_hash": prev, "event": event}
        entry["entry_hash"] = sha(canon(entry).encode())
        with open(self.audit_path, "a") as f: f.write(json.dumps(entry, sort_keys=True) + "\n")
        json.dump({"last": self.seq}, open(self.seq_path, "w"))
        return entry

    def verify_chain(self):
        prev = "GENESIS"; n = 0
        for ln in open(self.audit_path):
            e = json.loads(ln); h = e.pop("entry_hash")
            if e["prev_hash"] != prev: return False, n, "quebra de cadeia"
            if sha(canon(e).encode()) != h: return False, n, "hash adulterado"
            prev = h; n += 1
        return True, n, "ok"

    # ---------- autorizacao (nega por padrao) ----------
    def authorize(self, req):
        """req: program_sha256, capabilities[], seconds, execution_id, purpose."""
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        try:
            if self.policy.get("default_effect") != "deny":
                raise Denied("POLICY_INVALID", "politica sem negacao por padrao")
            if now > self.policy.get("valid_until", "9999"):
                raise Denied("POLICY_EXPIRED", self.policy.get("valid_until"))
            if req["execution_id"] in self.seen:
                raise Denied("REPLAY_DETECTED", req["execution_id"])
            grant = None
            for g in self.policy.get("grants", []):
                if g["program_sha256"] == req["program_sha256"]: grant = g; break
            if grant is None:
                raise Denied("POLICY_PROGRAM_NOT_ALLOWED", req["program_sha256"][:16])
            if grant.get("revoked"):
                raise Denied("GRANT_REVOKED", grant["grant_id"])
            if now > grant.get("expires_at", "9999"):
                raise Denied("GRANT_EXPIRED", grant.get("expires_at"))
            falta = [c for c in req.get("capabilities", []) if c not in grant.get("capabilities", [])]
            if falta:
                raise Denied("CAPABILITY_NOT_GRANTED", ",".join(falta))
            lim = min(grant.get("max_seconds", 0), self.policy.get("limits", {}).get("max_seconds", 0))
            if req.get("seconds", 0) > lim:
                raise Denied("LIMIT_EXCEEDED", f"pedido {req.get('seconds')}s > limite {lim}s")
            pre = {
                "receipt": "pre", "receipt_version": "v1",
                "policy_version": self.policy["policy_version"],
                "grant_id": grant["grant_id"],
                "execution_id": req["execution_id"],
                "program_sha256": req["program_sha256"],
                "capabilities": req.get("capabilities", []),
                "purpose": req.get("purpose", ""),
                "authorized_at": now,
            }
            pre["receipt_hash"] = sha(canon(pre).encode())
            self._audit({"kind": "AUTHORIZED", **pre})
            self.seen.append(req["execution_id"]); json.dump(self.seen, open(self.seen_path, "w"))
            return pre
        except Denied as d:
            ref = {"receipt": "refusal", "receipt_version": "v1",
                   "execution_id": req.get("execution_id"), "denial_code": d.code,
                   "detail": d.detail, "at": now,
                   "execution_state": "NOT_EXECUTED", "verdict": "REFUSED",
                   "signature": "NONE (integridade por hash; autenticidade = M4)"}
            ref["receipt_hash"] = sha(canon(ref).encode())
            self._audit({"kind": "REFUSED", **ref})
            return ref

    # ---------- execucao sob autorizacao ----------
    def execute(self, req, fn):
        pre = self.authorize(req)
        if pre["receipt"] == "refusal":
            return {"pre": None, "refusal": pre, "executed": False, "result": None}
        limite = req.get("seconds", 0)
        def _timeout(s, f): raise TimeoutError("limite de tempo excedido")
        old = signal.signal(signal.SIGALRM, _timeout); signal.alarm(max(1, int(limite)))
        t0 = time.time()
        try:
            out = fn()
            signal.alarm(0); state, verdict, res = "SUCCESS", "COMPUTED", out
        except Exception as e:
            signal.alarm(0); state, verdict, res = "INTERRUPTED", "ERROR", f"{type(e).__name__}: {e}"
        finally:
            try: signal.signal(signal.SIGALRM, old)
            except Exception: pass
        post = {"receipt": "post", "receipt_version": "v1", "execution_id": req["execution_id"],
                "prev_receipt_hash": pre["receipt_hash"], "execution_state": state,
                "verdict": verdict, "elapsed_s": round(time.time() - t0, 4),
                "result_sha256": sha(canon(res).encode()) if res is not None else None}
        post["receipt_hash"] = sha(canon(post).encode())
        self._audit({"kind": "EXECUTED", **post})
        return {"pre": pre, "refusal": None, "executed": True, "result": res, "post": post}
