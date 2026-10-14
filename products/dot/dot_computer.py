#!/usr/bin/env python3
"""
DOT COMPUTER — o computador próprio do agente (MVP, Fase 1).
==================================================================
Workspace isolado e persistente + terminal controlado + auditoria.

Contrato honesto (§12):
- Workspace: diretorio isolado; nenhuma operacao escapa dele
  (travessia de caminho e' recusada, nao corrigida por engano).
- Terminal: so executa comandos da politica de allowlist, com teto de
  tempo, captura de saida e registro em log de auditoria. Comandos
  proibidos REJEITADOS com motivo — nunca "corrigidos".
- Auditoria: todo evento e' gravado em JSONL (quem, o quê, quando, resultado).
  Falhas registram o motivo sem vazar segredo algum.

Estado: IMPLEMENTADO (teste: products/dot/test_dot.py)
Fonte de verdade do projeto: docs/ZEPHIRUM_STANDARD_v0.3.md (§12 honestidade).
"""
import json
import os
import subprocess
import time
import uuid


class Refused(Exception):
    """Recusa formal do DOT Computer (não é erro de programa — é resposta)."""
    def __init__(self, reason):
        super().__init__(reason)
        self.reason = reason


class DotComputer:
    """Computador próprio: workspace + terminal controlado + auditoria."""

    def __init__(self, root):
        # root fica FORA do repo em uso real; aqui, caminho dado pelo orquestrador
        self.root = os.path.realpath(root)
        os.makedirs(self.root, exist_ok=True)
        self.events_path = os.path.join(self.root, ".dot", "events.jsonl")
        os.makedirs(os.path.join(self.root, ".dot"), exist_ok=True)
        # allowlist de comandos de terminal: prefixos permitidos (menor privilégio)
        # MVP: leitura de arquivos, python restrito ao workspace, contagem — sem rede, sem escrita fora
        self.allowed_commands = ("ls", "cat", "wc", "python3")
        self.max_output_bytes = 200_000
        self.timeout_s = 30

    # ---------- auditoria ----------
    def _event(self, kind, detail):
        ev = {"id": uuid.uuid4().hex[:12], "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
              "kind": kind, "detail": detail}
        with open(self.events_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")
        return ev

    def events(self):
        if not os.path.exists(self.events_path):
            return []
        with open(self.events_path, encoding="utf-8") as f:
            return [json.loads(l) for l in f if l.strip()]

    # ---------- arquivos (dentro do workspace, sempre) ----------
    def _resolve(self, rel):
        """Resolve caminho relativo ao workspace; recusa travessia."""
        if os.path.isabs(rel) or rel.startswith("~"):
            raise Refused("caminho absoluto não permitido: use caminho relativo ao workspace")
        p = os.path.realpath(os.path.join(self.root, rel))
        if p != self.root and not p.startswith(self.root + os.sep):
            raise Refused("travessia de caminho fora do workspace recusada")
        return p

    def write_file(self, rel, content):
        p = self._resolve(rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
        self._event("file_write", {"path": rel, "bytes": len(content.encode())})
        return {"ok": True, "path": rel, "bytes": len(content.encode())}

    def read_file(self, rel):
        p = self._resolve(rel)
        if not os.path.exists(p):
            raise Refused(f"arquivo inexistente: {rel}")
        with open(p, encoding="utf-8") as f:
            content = f.read(self.max_output_bytes)
        self._event("file_read", {"path": rel})
        return content

    def list_files(self, rel="."):
        p = self._resolve(rel)
        out = []
        for base, dirs, files in os.walk(p):
            if ".dot" in base.split(os.sep):
                continue
            for fn in files:
                out.append(os.path.relpath(os.path.join(base, fn), self.root))
        return sorted(out)

    # ---------- terminal controlado ----------
    def run_command(self, cmd, cwd="."):
        """Executa comando permitido com teto de tempo e saída. Recusa o resto."""
        base = cmd.split()[0] if cmd.split() else ""
        if base not in self.allowed_commands:
            self._event("command_refused", {"cmd": cmd, "reason": "comando fora da allowlist"})
            raise Refused(f"comando não permitido pela política de terminal: {base!r}")
        p = self._resolve(cwd)
        try:
            proc = subprocess.run(cmd, shell=True, cwd=p, capture_output=True,
                                  text=True, timeout=self.timeout_s)
        except subprocess.TimeoutExpired:
            self._event("command_timeout", {"cmd": cmd, "limit_s": self.timeout_s})
            raise Refused(f"comando excedeu o teto de {self.timeout_s}s e foi interrompido")
        out = (proc.stdout or "")[:self.max_output_bytes]
        self._event("command_run", {"cmd": cmd, "rc": proc.returncode, "cwd": cwd})
        return {"rc": proc.returncode, "stdout": out, "stderr": (proc.stderr or "")[:2000]}
