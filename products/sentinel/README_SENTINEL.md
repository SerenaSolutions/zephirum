# ZYQL SENTINEL + PROOFCHAIN — MVP (Produtos P1 + P3)

**Estado: `IMPLEMENTADO` + `TESTADO`** (bateria 12/12 PASS, `test_sentinel.py`; executada
também pelo CI). Serviço rodando: `python3 sentinel_server.py [porta]`.

## O que é

O primeiro MVP comercial do portfólio ZYQL: uma **API de decisões verificáveis**
(Sentinel) sobre o núcleo trivalente exato do ZEPHIRUM, emitindo **recibos
encadeados e assinados** (ProofChain). O valor existe HOJE, com execução 100%
clássica — nenhum QPU no caminho (§12: o kernel decide exatamente offline).

## Semântica normativa

| Veredito | Significado |
|---|---|
| `1` | Condição satisfeita, evidência suficiente, certificado verificado |
| `0` | Condição não satisfeita, evidência suficiente, certificado verificado |
| `REFUSED` | Recusa estrutural explícita (contrato inválido, escopo, purpose) — nunca crash |
| `UNKNOWN` | Evidência insuficiente — **nunca vira palpite** |

## Endpoints

| Método | Rota | Função |
|---|---|---|
| GET | `/v1/health` | estado, modo de assinatura, cabeça da cadeia |
| POST | `/v1/decide` | `{"program": "<fonte ZEPHIRUM>", "question_id": opcional}` → decisão + recibo |
| POST | `/v1/verify` | `{"receipt": {...}}` → verificação independente (`RECEIPT_VALID` / `REJECT: motivo`) |
| GET | `/v1/chain/head` | hash da cabeça da cadeia + contagem de recibos |

## Exemplo

```bash
$ curl -s http://127.0.0.1:8091/v1/health
{"status": "ok", "kernel": "ZEPHIRUM nexa_core (trivalente exato)",
 "signing": "ML-DSA-44 (FIPS 204)", "chain_head": "d4c68bc0...", "receipts": 7}

$ curl -s -X POST http://127.0.0.1:8091/v1/decide -H "Content-Type: application/json" \
  -d '{"program":"ASK:\n    question: sum > 50\nCONTRACT:\n    absolute_error: 0\nMODEL:\n    type: threshold_sum\n    terms: 60, 30, 20, 5\n    assumption: terms_nonnegative"}'
{"decision": {"verdict": "1", "status": "DECIDED_BY_REDUCTION",
              "eliminated_units": 3, "original_units": 4, ...},
 "receipt": {"RECEIPT_HASH": "551a0cc3...", "PREV_HASH": "d4c68bc0...",
             "signature": {"algorithm": "ML-DSA-44", "fips": "204"}, ...}}
```

## O que o recibo prova (e o que NÃO prova)

- **PROVA**: integridade (qualquer alteração do corpo quebra o hash), encadeamento
  (cada recibo sela o anterior — romper um quebra todos os seguintes),
  autenticidade do emissor (ML-DSA-44 / FIPS 204, imune a Shor) e presença na
  cadeia real (anti-replay).
- **NÃO PROVA sozinho**: a correção científica do conteúdo. `RECEIPT_VALID` ≠
  `SCIENTIFIC_RESULT_VALID`. A correção vem do certificado do kernel, verificável
  de forma independente (`prototype/verify_certificate.py`), e o Sentinel RECUSA
  qualquer decisão cujo certificado o próprio checker rejeite.

## §12 — honestidade incorporada

- Sem `pqcrypto`, os recibos saem `unsigned-explicit` — **nunca** fingimos assinatura.
- A bateria forja recibos de dois jeitos (conteúdo e elo) e exige `REJECT` nos dois.
- Exit code da bateria propaga falha (0 só com todos PASS).

## Bateria

```
S1 decisão "1" assinada    S2 decisão "0"    S3 UNKNOWN honesto    S4 REFUSED estrutural
S5 recibo válido           S6 forja REJECT  S7 elo forjado REJECT  S8 encadeamento real
S9 API HTTP end-to-end (/v1/decide + /v1/verify)
```

## Arquitetura (reuso, zero reescrita)

- `prototype/nexa_core.py` — kernel trivalente exato (suíte v0.3 + auditoria independente)
- `prototype/verify_certificate.py` — checker independente
- `products/sentinel/proofchain.py` — cadeia SHA-256 + assinatura ML-DSA-44
- `products/sentinel/sentinel_server.py` — API REST stdlib-only
- Chaves nunca saem do diretório local (`sentinel_keys/`, gitignored)
