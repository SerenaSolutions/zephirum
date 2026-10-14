#!/usr/bin/env python3
"""
DOT ORCHESTRATOR — o ciclo controlado do agente (MVP, Fases 1+2+6).
==================================================================
Ciclo: objetivo -> plano -> autorização ZYQL -> execução no computador
próprio -> verificação -> checkpoint -> recibo -> limite/retomada.

Planejador: MVP usa plano declarado (determinístico). O adaptador LLM
é interface explícita BLOQUEADA até provedor/credencial definidos (§12:
não fingimos planejamento probabilístico com um stub).

Persistência: task.json + checkpoints por passo. O orquestrador pode
cair e RETOMAR do último checkpoint (teste D6 reinicia e retoma).

Recibos: ProofChain (ML-DSA-44 real quando pqcrypto disponível) —
reutiliza o módulo do produto Sentinel: um recibo, vários produtos.

Estado: IMPLEMENTADO (teste: products/dot/test_dot.py)
"""
import json
import os
import time
import uuid

from dot_computer import DotComputer, Refused
from dot_policy import TrivalentPolicy, load_policy

HERE = os.path.dirname(os.path.abspath(__file__))
sys_path_hack = os.path  # noqa — clareza
import sys
sys.path.insert(0, os.path.join(HERE, "..", "sentinel"))
from proofchain import ProofChain  # reuso do produto P3 (PR #8)


class LLMPlanner:
    """Interface do planejador neural. MVP: BLOQUEADO — plano declarado.

    Um provedor real (API de LLM) retorna DOT-PLAN: subtarefas com
    tool/args/critério. A saída do modelo é PROPOSTA não confiável:
    cada passo ainda passa pela TrivalentPolicy antes de executar.
    """

    def plan(self, objective):
        raise NotImplementedError(
            "adaptador LLM bloqueado: nenhum provedor/credencial definido "
            "(§12 — não simulamos planejamento)")


class DotTask:
    """Estado persistente de uma tarefa + checkpoints."""

    def __init__(self, workspace, task_id=None):
        self.ws = workspace
        self.task_id = task_id or ("dot-" + uuid.uuid4().hex[:8])
        self.dir = os.path.join(workspace, ".dot", "tasks", self.task_id)
        os.makedirs(self.dir, exist_ok=True)
        self.state_path = os.path.join(self.dir, "task.json")

    def save(self, state):
        with open(self.state_path, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=1)

    def load(self):
        if not os.path.exists(self.state_path):
            return None
        with open(self.state_path, encoding="utf-8") as f:
            return json.load(f)

    def checkpoint(self, step_index, note):
        cp = {"step": step_index, "note": note,
              "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        with open(os.path.join(self.dir, "checkpoint.json"), "w", encoding="utf-8") as f:
            json.dump(cp, f)
        return cp


class DotAgent:
    """O agente: tem computador, política, cadeia de recibos e limites."""

    def __init__(self, computer: DotComputer, policy: TrivalentPolicy, ledger_path=None, keydir=None):
        self.computer = computer
        self.policy = policy
        # keydir próprio do DOT (dentro do workspace, nunca commitado): assinatura
        # ML-DSA-44 REAL quando pqcrypto existe; sem pqcrypto: unsigned-explicit (§12)
        self.chain = ProofChain(
            ledger_path or os.path.join(computer.root, ".dot", "proofchain.jsonl"),
            keydir or os.path.join(computer.root, ".dot", "keys"))
        self.limits = {"max_steps": 25, "deadline_s": 120, "max_tool_calls": 15}

    def run(self, plan, task_id=None, resume=True):
        """plan = {"objective": str, "steps": [{"tool","args","expect_rc":0?}]}"""
        task = DotTask(self.computer.root, task_id)
        state = task.load() if resume else None
        if state is not None and state.get("status", "").startswith("stopped"):
            state["status"] = "running"  # retomada: limite anterior não carrega para a nova sessão
        if state is None:
            state = {"objective": plan["objective"], "step": 0, "status": "running",
                     "results": [], "tool_calls": 0, "started_ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        steps = plan["steps"]
        t0 = time.time()
        last_receipt = None
        while state["step"] < len(steps):
            if state["step"] >= self.limits["max_steps"]:
                state["status"] = "stopped_limit"; break
            if time.time() - t0 > self.limits["deadline_s"]:
                state["status"] = "stopped_deadline"; break
            if state["tool_calls"] >= self.limits["max_tool_calls"]:
                state["status"] = "stopped_budget"; break
            step = steps[state["step"]]
            ikey = f"{task.task_id}:{state['step']}"  # idempotência: passo executado 1x
            action = {"tool": step["tool"], "args": step.get("args", {}),
                      "idempotency_key": ikey, "evidence": step.get("evidence", [])}
            verdict, reason = self.policy.evaluate(action)
            receipt = self.chain.issue({"task": task.task_id, "step": state["step"],
                                        "tool": step["tool"], "verdict": verdict,
                                        "reason": reason})
            last_receipt = receipt
            if verdict != "1":
                state["status"] = "refused"
                state["refusal"] = {"step": state["step"], "reason": reason}
                task.save(state); task.checkpoint(state["step"], f"recusado: {reason}")
                return state, receipt
            # execução no computador próprio
            try:
                result = self._execute(step)
            except Refused as r:
                state["status"] = "refused"
                state["refusal"] = {"step": state["step"], "reason": r.reason}
                task.save(state); task.checkpoint(state["step"], f"recusado: {r.reason}")
                return state, receipt
            state["results"].append({"step": state["step"], "tool": step["tool"], "rc": result.get("rc", 0)})
            state["tool_calls"] += 1
            state["step"] += 1
            task.save(state)
            task.checkpoint(state["step"], f"passo {state['step']} concluído")
        state["status"] = "done" if state["status"] == "running" else state["status"]
        task.save(state)
        return state, last_receipt

    def _execute(self, step):
        tool, args = step["tool"], step.get("args", {})
        if tool == "write_file":
            return self.computer.write_file(args["path"], args["content"])
        if tool == "read_file":
            return {"ok": True, "content": self.computer.read_file(args["path"])}
        if tool == "run_command":
            return self.computer.run_command(args["cmd"], args.get("cwd", "."))
        raise Refused(f"ferramenta sem executor no runtime: {tool!r}")
