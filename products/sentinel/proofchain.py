#!/usr/bin/env python3
"""PROOFCHAIN — infraestrutura de recibos encadeados e assinados (produto ZYQL ProofChain).

Estado: IMPLEMENTADO + TESTADO (bateria test_sentinel.py)
§12 — honestidade estrutural:
  - Assinatura ML-DSA-44 (FIPS 204) REAL via pqcrypto quando disponível;
  - SEM pqcrypto: o recibo sai como "unsigned-explicit" — nunca fingimos assinatura;
  - Encadeamento por SHA-256: cada recibo sela o hash do anterior (PREV_HASH);
  - A assinatura prova INTEGRIDADE e AUTENTICIDADE do emissor conforme as chaves;
    NÃO prova, sozinha, a correção científica do conteúdo (RECEIPT_VALID !=
    SCIENTIFIC_RESULT_VALID — distinção preservada em toda a API).
"""
import base64
import datetime
import hashlib
import json
import os
import threading

ALG = "ML-DSA-44"
FIPS = "204"
GENESIS = "0" * 64

try:
    from pqcrypto.sign import ml_dsa_44
    SIGNING_OK = True
except ImportError:
    ml_dsa_44 = None
    SIGNING_OK = False


def utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def canonical(payload):
    """Bytes canônicos do payload JSON: chaves ordenadas, sem espaços."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def sha256(data):
    if isinstance(data, dict) or isinstance(data, list):
        data = canonical(data)
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _b64(b):
    return base64.b64encode(b).decode()


def _unb64(s):
    return base64.b64decode(s)


def load_keypair(keydir):
    """Carrega (pub, priv) de keydir; gera e persiste se não existir (não commitado)."""
    pub_p = os.path.join(keydir, "sentinel_ml_dsa_44.pub")
    priv_p = os.path.join(keydir, "sentinel_ml_dsa_44.priv")
    if os.path.exists(pub_p) and os.path.exists(priv_p):
        with open(pub_p, "rb") as f:
            pub = f.read()
        with open(priv_p, "rb") as f:
            priv = f.read()
        return pub, priv
    pub, priv = ml_dsa_44.keygen()
    os.makedirs(keydir, exist_ok=True)
    with open(pub_p, "wb") as f:
        f.write(pub)
    with open(priv_p, "wb") as f:
        f.write(priv)
    gi = os.path.join(keydir, ".gitignore")
    with open(gi, "w") as f:
        f.write("*.priv\n*.pub\n")
    return pub, priv


class ProofChain:
    """Cadeia append-only de recibos: cada recibo sela o hash do anterior."""

    def __init__(self, ledger_path="proofchain.jsonl", keydir=None):
        self.path = ledger_path
        self.lock = threading.Lock()
        self.receipts = []
        self.keydir = keydir
        self.pub = self.priv = None
        if SIGNING_OK and keydir:
            self.pub, self.priv = load_keypair(keydir)
        # reconstrói a cabeça da cadeia a partir do ledger existente (replay-safe)
        prev = GENESIS
        if os.path.exists(ledger_path):
            with open(ledger_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    r = json.loads(line)
                    assert r["RECEIPT_HASH"] == self._body_hash(r["body"], prev), \
                        "ledger corrompido: hash nao bate (§12 — falha explicita)"
                    prev = r["RECEIPT_HASH"]
                    self.receipts.append(r)
        self.prev_hash = prev

    @staticmethod
    def _body_hash(body, prev):
        return sha256({"prev": prev, "body": body})

    def issue(self, body):
        """Emite recibo para `body` (dict de decisão), encadeado e assinado quando possível."""
        with self.lock:
            prev = self.prev_hash
            rh = self._body_hash(body, prev)
            receipt = {
                "protocol": "ZYQL-PROOFCHAIN/1",
                "ts_utc": utc(),
                "PREV_HASH": prev,
                "RECEIPT_HASH": rh,
                "body": body,
            }
            if self.priv is not None:
                sig = ml_dsa_44.sign(self.priv, canonical(receipt))
                receipt["signature"] = {
                    "algorithm": ALG, "fips": FIPS,
                    "public_key": _b64(self.pub), "value": _b64(sig),
                }
            else:
                # §12: sem pqcrypto nao há assinatura — declaração explicita, nunca fingimento
                receipt["signature"] = {
                    "algorithm": "unsigned-explicit",
                    "note": "pqcrypto ausente: recibo com integridade de cadeia, "
                            "SEM assinatura (TrustNotAvailable — nada é forjado)",
                }
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(receipt, ensure_ascii=False) + "\n")
            self.receipts.append(receipt)
            self.prev_hash = rh
            return receipt

    def verify(self, receipt, expect_prev=None):
        """Verificação INDEPENDENTE de um recibo (não confia no emitente).

        Checa: estrutura, encadeamento (PREV_HASH / RECEIPT_HASH recalculados),
        assinatura ML-DSA-44 quando declarada, e presença na cadeia real.
        Retorna (ok, reason). Nunca quebra; recusa explicita.
        """
        try:
            if receipt.get("protocol") != "ZYQL-PROOFCHAIN/1":
                return False, "REJECT: protocolo desconhecido"
            body = receipt["body"]
            prev = receipt["PREV_HASH"]
            rh = receipt["RECEIPT_HASH"]
            if self._body_hash(body, prev) != rh:
                return False, "REJECT: hash do recibo nao bate (conteudo ou cadeia adulterados)"
            if expect_prev is not None and prev != expect_prev:
                return False, "REJECT: elo PREV_HASH nao corresponde ao recibo anterior esperado"
            sig = receipt.get("signature", {})
            if sig.get("algorithm") == ALG:
                if ml_dsa_44 is None:
                    return False, "REJECT: recibo assinado, mas verificador sem pqcrypto"
                try:
                    ml_dsa_44.verify(_unb64(sig["public_key"]),
                                     canonical({k: receipt[k] for k in
                                                ("protocol", "ts_utc", "PREV_HASH",
                                                 "RECEIPT_HASH", "body")}),
                                     _unb64(sig["value"]))
                except Exception:
                    return False, "REJECT: assinatura ML-DSA-44 INVALIDA"
            elif sig.get("algorithm") != "unsigned-explicit":
                return False, "REJECT: algoritmo de assinatura inaceitavel"
            # cadeia real: o recibo tem que estar no ledger com o mesmo hash
            hashes = [r["RECEIPT_HASH"] for r in self.receipts]
            if rh not in hashes:
                return False, "REJECT: recibo nao consta na cadeia (replay/forja)"
            return True, "RECEIPT_VALID"
        except (KeyError, TypeError, ValueError) as e:
            return False, "REJECT: recibo malformado: %s" % e

    def head(self):
        return self.prev_hash

    def size(self):
        return len(self.receipts)
