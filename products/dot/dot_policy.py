#!/usr/bin/env python3
"""
DOT POLICY — adaptador ZYQL de decisões do agente (Fase 4 antecipada no MVP).
==================================================================
ADAPTADOR EXPLÍCITO (§12): a linguagem ZYQL real decide famílias
matemáticas certificadas (ver SCIENTIFIC_TECHNICAL_AUDIT.md). Este módulo
aplica a MESMA semântica trivalente (1 / 0 / REFUSED) ao domínio de
autorização de ações, com política declarada em JSON. Não simula o kernel:
quando a pergunta é matemática certificável, o kernel real é chamado.

Semântica normativa (idêntica ao README Sentinel):
- 1       : condição da política satisfeita e evidências suficientes.
- 0       : condição avaliada e NÃO satisfeita (negação, não recusa).
- REFUSED : permissão ausente, evidência insuficiente ou regra ambígua.

Conteúdo de arquivos, páginas e documentos NUNCA é fonte de autorização
(prompt injection: instruções encontradas não alteram política).

Estado: IMPLEMENTADO (teste: products/dot/test_dot.py)
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "prototype"))
sys.path.insert(0, os.path.join(HERE, "..", "sentinel"))

RISK_HIGH = {"external_write", "publish", "payment", "permission_change",
             "secret_access", "infrastructure", "delete"}
REQUIRES_HUMAN = RISK_HIGH  # MVP: risco alto sempre exige humano


def load_policy(path=None):
    """Política declarada: ferramentas permitidas e níveis de risco."""
    if path is None:
        path = os.path.join(HERE, "policy.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


class TrivalentPolicy:
    """O árbitro: LLM propõe, política decide. Nada executa sem 1."""

    def __init__(self, policy, human_approvals=None):
        self.p = policy
        # aprovações humanas concedidas nesta sessão (id => True)
        self.human_approvals = dict(human_approvals or {})

    def evaluate(self, action):
        """action = {"tool": str, "args": dict, "risk": str (opcional),
                     "evidence": list (opcional), "idempotency_key": str}."""
        tool = action.get("tool", "")
        risk = action.get("risk", self.p["tools"].get(tool, {}).get("risk", "unknown"))
        reasons = []

        # 1) ferramenta existe na política?
        if tool not in self.p["tools"]:
            return "REFUSED", "ferramenta não consta na política (fail-closed)"

        # 2) permissão de risco alto exige aprovação humana registrada
        if risk in REQUIRES_HUMAN and not self.human_approvals.get(action.get("idempotency_key")):
            return "REFUSED", f"risco '{risk}' exige aprovação humana (ausente)"

        # 3) evidência mínima declarada pela política presente?
        need = self.p["tools"][tool].get("requires_evidence", [])
        have = action.get("evidence") or []
        missing = [k for k in need if k not in have]
        if missing:
            return "REFUSED", f"evidência insuficiente: falta {missing}"

        # 4) condição declarada (vocabulário estrito, SEM eval — §12)
        cond = self.p["tools"][tool].get("condition")
        if cond is not None:
            ok, why = self._rule(cond, action.get("args", {}))
            if ok is None:
                return "REFUSED", f"regra ambígua/inválida: {why}"
            if not ok:
                return "0", f"condição da política avaliada como falsa: {why} (negação, não recusa)"

        # 5) rate limit por ferramenta (orçamento de ações)
        return "1", "política satisfeita; permissões e evidências presentes"

    _RULES = {
        "not_startswith": lambda v, x: (not str(v).startswith(str(x)), "campo começa com valor proibido"),
        "startswith": lambda v, x: (str(v).startswith(str(x)), "campo não começa com o valor exigido"),
        "eq": lambda v, x: (v == x, "campo difere do valor exigido"),
        "gt": lambda v, x: (isinstance(v, (int, float)) and v > x, "campo não excede o valor exigido"),
    }

    def _rule(self, cond, args):
        """Avalia regra declarada. Retorna (bool, motivo) ou (None, motivo_do_erro)."""
        if not isinstance(cond, dict) or cond.get("rule") not in self._RULES:
            return None, f"regra desconhecida: {cond!r}"
        if cond["field"] not in args:
            return None, f"campo ausente nos argumentos: {cond['field']!r}"
        fn = self._RULES[cond["rule"]]
        try:
            return fn(args[cond["field"]], cond.get("value"))
        except Exception as e:
            return None, f"falha ao avaliar regra: {type(e).__name__}"

    # ----- decisões matemáticas vão ao KERNEL REAL, nunca ao adaptador -----
    def kernel_decide(self, program_src):
        """Pergunta certificável (limiar/soma/média/série/emaranhamento):
        o ZYQL real decide, com certificado e checker independente."""
        from nexa_core import parse_nexa, NCA
        from verify_certificate import verify
        blocks = parse_nexa(program_src)
        res = NCA(blocks, "dot-kernel").compile()
        ok, why = verify(blocks, res["certificate"])
        if not ok:
            return "REFUSED", f"checker independente rejeitou: {why}"
        if res["status"] == "UNKNOWN":
            return "REFUSED", "kernel: UNKNOWN (não vira palpite)"
        return ("1" if res["answer"] else "0"), f"kernel: {res['kernel']} | checker: {why}"
