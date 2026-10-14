# DOT AGENT — MVP (Fases 1, 2, 4 e 6 do plano)

> **O LLM propõe. O conhecimento fundamenta. O agente executa. O ZYQL decide. O recibo prova.**

Primeira implementação do **DOT — Decision, Orchestration & Traceability** (protocolo
`DOT/0.1`, proposto — não padrão estabelecido). Agente com **computador próprio
persistente**, política trivalente e recibos assinados.

## Estado honesto por componente (§12)

| Componente | Estado | Nota |
|---|---|---|
| DOT Computer (workspace isolado + terminal controlado) | `IMPLEMENTADO` | travessia/absoluto recusados; allowlist; teto de tempo |
| DOT Policy (adaptador trivalente) | `IMPLEMENTADO` | adaptador EXPLÍCITO — política JSON, sem eval; decisões matemáticas vão ao KERNEL REAL |
| DOT Orchestrator (ciclo + limites + checkpoints) | `IMPLEMENTADO` | retomada após queda testada (D6) |
| DOT Receipts (ProofChain ML-DSA-44) | `IMPLEMENTADO` | reuso do produto Sentinel (PR #8); forja rejeitada |
| Memória de tarefas persistente | `IMPLEMENTADO` | task.json + checkpoint por passo |
| LLM Planner | `BLOQUEADO` | interface explícita `NotImplementedError` — nenhum provedor/credencial definido; não simulamos planejamento |
| RAG/CAG/KAG | `PROPOSTO` | camada de conhecimento: fase 3 do plano |
| Multiagente | `PROPOSTO` | fase 8 |
| QPU opcional | `PROPOSTO` | fase 7 — plataforma funciona 100% clássica |

## Semântica de decisão (normativa)

- `1` — condição da política satisfeita e evidências suficientes.
- `0` — condição avaliada como **falsa** (negação; a ação não segue).
- `REFUSED` — permissão ausente, evidência insuficiente, risco alto sem
  aprovação humana, ou regra ambígua. **Nunca vira palpite.**

**Anti prompt-injection (testado, caso D5):** conteúdo de arquivos, páginas e
documentos **nunca** altera a política. "GRANT ALL PERMISSIONS" dentro de um
documento não concede nada.

## Arquitetura mínima

```
DotAgent.run(plan)
  ├─ TrivalentPolicy.evaluate(action)     # 1/0/REFUSED — nada executa sem "1"
  ├─ DotComputer.write/read/run_command    # computador próprio isolado
  ├─ DotTask.save + checkpoint             # persistência por passo
  └─ ProofChain.issue(...)                 # recibo ML-DSA-44 encadeado
```

## Uso

```bash
python3 products/dot/test_dot.py   # bateria de aceitação (14 casos)
```

```python
from dot_computer import DotComputer
from dot_policy import TrivalentPolicy, load_policy
from dot_agent import DotAgent

pc = DotComputer("./dot_workspace")        # computador próprio (isolado)
ag = DotAgent(pc, TrivalentPolicy(load_policy()))
state, receipt = ag.run({
    "objective": "exemplo",
    "steps": [
        {"tool": "write_file", "args": {"path": "a.txt", "content": "olá"}},
        {"tool": "read_file", "args": {"path": "a.txt"}, "evidence": []},
    ],
})
```

## O que o recibo prova (e o que não prova)

O recibo ML-DSA-44 prova **integridade, autenticidade do emissor e encadeamento**
da execução registrada. **Não** prova sozinho que a conclusão é cientificamente
correta (`RECEIPT_VALID` ≠ `SCIENTIFIC_RESULT_VALID`).

## Limitações conhecidas do MVP

- Planejador é plano declarado; LLM exige provedor (decisão do dono).
- Risco alto exige aprovação humana registrada — interface de aprovação é
  programática no MVP (`human_approvals`).
- Browser automation, CAG, KAG e backends quânticos: ainda não implementados
  (fases 3, 7).
