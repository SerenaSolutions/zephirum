#!/usr/bin/env python3
"""ZYQL SENTINEL — API de decisões verificáveis (MVP do produto P1+P3).

Estado: IMPLEMENTADO (MVP) — kernel de decisão reutilizado do ZEPHIRUM
(nexa_core, TESTADO pela suíte v0.3 e auditoria independente 2026-10-13).

Semântica trivalente exposta pela API (tabela normativa):
    verdict "1"       — condição satisfeita, evidência suficiente (decisão certificada)
    verdict "0"       — condição não satisfeita, evidência suficiente (decisão certificada)
    verdict "REFUSED" — estrutura/purpose/escopo inválidos: recusa EXPLÍCITA
    verdict "UNKNOWN" — evidência insuficiente para decidir (nunca vira palpite)

Cada decisão emite recibo ZYQL-PROOFCHAIN/1 (encadeado por SHA-256; assinado
ML-DSA-44 quando pqcrypto disponível). Endpoints:

    GET  /v1/health          — estado do serviço e modo de assinatura
    POST /v1/decide          — {"program": "<fonte ZEPHIRUM nexa>"} -> decisão + recibo
    POST /v1/verify          — {"receipt": {...}} -> verificação independente do recibo
    GET  /v1/chain/head      — hash da cabeça da cadeia e nº de recibos

Execução: python3 sentinel_server.py [porta]   (stdlib only; sem QPU no caminho)
§12 — nunca fingir: sem pqcrypto, recibos saem "unsigned-explicit"; decisões
quânticas não são invocadas aqui (o kernel decide EXATAMENTE offline).
"""
import json
import os
import sys

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "prototype"))

from nexa_core import parse_nexa, NCA            # noqa: E402  (kernel TESTADO)
from verify_certificate import verify            # noqa: E402  (checker independente)

from proofchain import ProofChain, SIGNING_OK    # noqa: E402

LEDGER = os.path.join(HERE, "proofchain.jsonl")
KEYDIR = os.path.join(HERE, "sentinel_keys")

CHAIN = ProofChain(LEDGER, keydir=KEYDIR if SIGNING_OK else None)


def decide(program_src, question_id=None):
    """Núcleo Sentinel: fonte ZEPHIRUM -> veredito trivalente + recibo encadeado."""
    record = {"product": "ZYQL-SENTINEL/1", "question_id": question_id}
    try:
        blocks = parse_nexa(program_src)
        res = NCA(blocks, "sentinel").compile()
    except ValueError as e:
        # recusa estrutural (purpose, contrato, vocabulário) — explicita, nunca crash
        record.update({"verdict": "REFUSED", "status": "STRUCTURAL_REFUSAL",
                       "reason": str(e)[:300], "certificate": None})
        return record, CHAIN.issue(record)
    status = res["status"]
    answer = res["answer"]
    if status == "UNKNOWN":
        verdict = "UNKNOWN"
    elif answer is True:
        verdict = "1"
    elif answer is False:
        verdict = "0"
    else:
        # estado imprevisto do kernel: recusa por honestidade (§12)
        verdict = "REFUSED"
    ok, reason = verify(blocks, res["certificate"])
    cert = res["certificate"]
    record.update({
        "verdict": verdict,
        "status": status,
        "kernel": res["kernel"],
        "rung": res["rung"],
        "eliminated_units": res["eliminated"],
        "original_units": res["original"],
        "checker": {"ok": ok, "reason": reason},
        "certificate": {
            "INPUT_HASH": cert["INPUT_HASH"],
            "CERT_HASH": cert["CERT_HASH"],
            "STATUS": cert["STATUS"],
        },
        "input_hash": cert["INPUT_HASH"],
        "certificate_hash": cert["CERT_HASH"],
        "input_sha256": __import__("hashlib").sha256(
            program_src.encode("utf-8")).hexdigest(),
    })
    if not ok:
        # um certificado que o próprio checker rejeita NÃO pode virar decisão vendida
        record["verdict"] = "REFUSED"
        record["status"] = "CHECKER_REJECTED"
    return record, CHAIN.issue(record)


class Handler(BaseHTTPRequestHandler):
    def _json(self, code, obj):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/v1/health":
            self._json(200, {
                "status": "ok",
                "kernel": "ZEPHIRUM nexa_core (trivalente exato)",
                "signing": "ML-DSA-44 (FIPS 204)" if SIGNING_OK else "unsigned-explicit",
                "chain_head": CHAIN.head(),
                "receipts": CHAIN.size(),
            })
        elif self.path == "/v1/chain/head":
            self._json(200, {"chain_head": CHAIN.head(), "receipts": CHAIN.size()})
        else:
            self._json(404, {"error": "endpoint desconhecido"})

    def do_POST(self):
        try:
            n = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(n) or b"{}")
        except (ValueError, json.JSONDecodeError):
            return self._json(400, {"error": "JSON malformado"})
        if self.path == "/v1/decide":
            program = body.get("program")
            if not isinstance(program, str) or not program.strip():
                return self._json(400, {"error": "campo 'program' obrigatorio (fonte ZEPHIRUM)"})
            record, receipt = decide(program, body.get("question_id"))
            return self._json(200, {"decision": record, "receipt": receipt})
        if self.path == "/v1/verify":
            receipt = body.get("receipt")
            if not isinstance(receipt, dict):
                return self._json(400, {"error": "campo 'receipt' obrigatorio"})
            ok, reason = CHAIN.verify(receipt)
            return self._json(200, {"ok": ok, "result": reason})
        return self._json(404, {"error": "endpoint desconhecido"})

    def log_message(self, fmt, *args):
        pass  # logs silenciosos no MVP; auditoria vive na cadeia de recibos


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8091
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print("ZYQL SENTINEL MVP — ouvindo em 127.0.0.1:%d" % port)
    print("assinatura:", "ML-DSA-44" if SIGNING_OK else "unsigned-explicit (§12)")
    print("cadeia:", CHAIN.size(), "recibos | head", CHAIN.head()[:16], "...")
    srv.serve_forever()


if __name__ == "__main__":
    main()
