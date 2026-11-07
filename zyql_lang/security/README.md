# ZYQL S2 — Policy Gate (negacao por padrao)

O porteiro da execucao: nada roda sem autorizacao explicita. Recusa acontece
ANTES da execucao e deixa recibo proprio (execution_state NOT_EXECUTED,
verdict REFUSED).

## O que este marco ENTREGA (IMPLEMENTADO, provado por bateria)
- negacao por padrao: politica sem grant -> REFUSED com codigo
- codigos de recusa: POLICY_PROGRAM_NOT_ALLOWED, CAPABILITY_NOT_GRANTED,
  GRANT_EXPIRED, GRANT_REVOKED, REPLAY_DETECTED, LIMIT_EXCEEDED, POLICY_EXPIRED
- recibo PREVIO (antes de executar) e POSTERIOR (referenciando o previo por hash)
- anti-replay: execution_id unico + sequencia monotona
- cadeia de auditoria verificavel (prev_hash) com deteccao de adulteracao
- limite de tempo com interrupcao -> execution_state INTERRUPTED, verdict ERROR
  (falha tecnica nunca e' rotulada como recusa)

## O que este marco NAO entrega (declarado, nao fingido)
- AUTENTICIDADE por chave: ESPECIFICACAO (M4). Aqui ha integridade (hash),
  nao assinatura. Recibo valido nao prova execucao segura.
- SANDBOX de SO: ESPECIFICACAO (S4). O gate autoriza; nao isola processo,
  arquivo ou rede. Zero-I/O exige S4 com testes de escape.
- ausencia de violacao registrada nao prova ausencia de violacao.

## Uso

```python
from policy_gate import PolicyGate
gate = PolicyGate("policy_v1.json", "state/")
r = gate.execute({"program_sha256": H, "capabilities": ["compute"],
                  "seconds": 1, "execution_id": "exec-001", "purpose": "..."}, funcao)
# r["refusal"] existe se recusado; r["post"]["verdict"] se executou
```

Bateria: `python3 test_s2_policy_gate.py` (12 casos, todos PASS).
Recibo: RECEIPT_S2.json (hash f0c5f221).
