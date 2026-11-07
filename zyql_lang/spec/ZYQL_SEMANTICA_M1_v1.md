# ZYQL — SEMÂNTICA V1 (MARCO M1) — DOCUMENTO DE CONGELAMENTO

Kernel de referência: ZEPHYRUM 1.12 · Estado do documento: CONGELADO PARA REVISÃO
Emissor: execução técnica · Revisão exigida: frente independente (ninguém aprova o que escreveu)

Regra editorial deste documento: cada item traz seu estado de maturidade —
IMPLEMENTADO (existe código + teste), PARCIAL (existe parte), ESPECIFICAÇÃO (definido aqui, sem
implementação), EXPERIMENTAL (funciona mas não certificável por instância).

---

## 1. CONTRATO CENTRAL

Toda execução ZYQL declara, antes de executar, seis campos. Sem os seis, o programa não roda.

| Campo | Tipo | Regra |
|---|---|---|
| entrada | domínio + dados | deve satisfazer as exigências declaradas em `contrato` |
| propósito | texto curto, verificável | descreve a pergunta, não a solução |
| critério | expressão booleana sobre evidência | determinístico e reproduzível |
| política | identificador versionado | resolve para um conjunto de regras de autorização |
| evidência | lista de artefatos exigidos | define o que será auditado |
| veredito | um dos 5 estados (§2) | produzido EXCLUSIVAMENTE pela regra aprovada |

Estado: ESPECIFICAÇÃO (o formato existe em ASK/CONTRACT/MODEL; os seis campos unificados não).

## 2. ESTADOS DE VEREDITO (5)

| Estado | Definição formal | Válido apenas se |
|---|---|---|
| 1 | O critério foi satisfeito dentro das condições declaradas | regra aprovada decidiu, evidência íntegra |
| 0 | O critério não foi satisfeito dentro das condições declaradas | regra aprovada decidiu, evidência íntegra |
| REFUSED | Política ou condição obrigatória impediu a decisão | política avaliada ANTES de executar |
| INCONCLUSIVE | A evidência disponível não permite decidir pela regra | margem de erro cruza a fronteira de decisão |
| ERROR | Falha técnica impediu a conclusão normal | falha registrada com artefato |

Regras de consistência:
- INCONCLUSIVE nunca pode ser emitido quando a regra tem poder estatístico declarado suficiente
  para decidir; e nunca pode ser silenciosamente convertido em 0.
- ERROR nunca é retroativamente reclassificado como REFUSED (e vice-versa). A recusa é decisão;
  a falha é acidente.
- Um veredito sem `decision_rule` identificada é inválido por construção.

Estado: IMPLEMENTADO para 1/0/REFUSED (parser + gates); ESPECIFICAÇÃO para INCONCLUSIVE/ERROR.

## 3. ESTADO DE EXECUÇÃO (separado do veredito)

| Estado | Significado |
|---|---|
| EXECUTED | o pipeline completou e o veredito foi produzido pela regra |
| DENIED | a política recusou ANTES de qualquer execução |
| INTERRUPTED | limites de recurso/tempo encerraram a execução |
| FAILED | erro técnico registrado |

Combinações válidas: (DENIED, REFUSED) · (EXECUTED, 1) · (EXECUTED, 0) · (EXECUTED, INCONCLUSIVE)
· (INTERRUPTED, ERROR) · (FAILED, ERROR).
Combinações inválidas: (DENIED, 1) · (EXECUTED, REFUSED) · (FAILED, 0).
Estado: ESPECIFICAÇÃO.

## 4. REGRAS DE DECISÃO VERSIONADAS

Formato: `nome-vN`, imutável após publicação. Uma alteração cria `nome-vN+1`; nunca se edita a regra.

Regra fundadora — `proporcao-v1`:
- Dados: S amostras iid de Bernoulli; alvo: proporção p; limiar t; confiança delta.
- Banda (Hoeffding): eps = sqrt( ln(2/delta) / (2S) ).
- Verdictos: 1 se (p_hat − eps) > t; 0 se (p_hat + eps) < t; INCONCLUSIVE se eps >= |p_hat − t|.
- Bordas: S = 0 -> ERROR de contrato (não INCONCLUSIVE); delta >= 1 ou <= 0 -> REFUSED por política;
  NaN em qualquer entrada -> ERROR.
Estado: IMPLEMENTADO como função e baterias de borda; PARCIAL como regra registrada em registry.

## 5. RECIBO V1

Formato público, versionado, verificável sem o programa que o produziu. Blocos:

IDENTIDADE: receipt_version, program_hash, language_version, compiler_version, policy_version
EXECUÇÃO: execution_id, sequence, input_commitment, environment, backend, parameters, start_time, end_time
EVIDÊNCIAS: evidence_hashes[], decision_rule, verdict, execution_state, uncertainty, limitations[]
AUTENTICIDADE: previous_receipt_hash, signer_key_id, signature_algorithm, signature

Regras:
- Recibo PRÉVIO assinado antes da execução (compromisso com programa, propósito, parâmetros, política).
- Recibo POSTERIOR referencia o prévio por hash e registra resultado e evidências.
- Anti-replay: execution_id único + sequence monotônica por emissor.
- Hash de entrada NÃO permite reconstruir a entrada; a assinatura autentica os dados assinados,
  não prova a verdade do resultado. Correção depende de evidência + regra + verificação.
Estado: PARCIAL (recibos com hash em todas as baterias; assinatura em recibos de hardware;
prévio, sequence e cadeia previous_receipt_hash = ESPECIFICAÇÃO).

Schema legível por máquina: `receipt_v1.schema.json` (neste diretório).

## 6. REGRAS DE TRANSIÇÃO (T1–T6)

T1 (não-clonagem): nenhum veredito existe sem recibo; copiar recibo sem a evidência correspondente
não reproduz o veredito.
T2 (monotonicidade de política): se a política NEGA, nenhuma execução ocorre; e não há veredito.
T3 (separação falha/decisão): ERROR não se converte em 0 nem em REFUSED.
T4 (inconclusão honesta): INCONCLUSIVE exige que a regra declare sua banda; a banda é parte do recibo.
T5 (cadeia íntegra): recibo posterior cujo previous_receipt_hash não casa com o prévio é INVÁLIDO.
T6 (regra imutável): veredito aponta para regra versionada; regra não editada retroativamente.

## 7. CASOS DE CONFORMIDADE (M1)

Ver `m1_conformance_cases.json`. Cada caso: id, requisito, entrada, veredito esperado,
estado de execução esperado, executável-hoje (true/false) e evidência exigida.

## 8. MATRIZ M1 — O QUE EXISTE E O QUE FALTA

| Requisito | Spec | Código | Teste | Estado |
|---|---|---|---|---|
| gramática formal | EBNF v1.0 | zyql_parser.py | 101/101 + 12/12 | IMPLEMENTADO |
| 3 estados base | §2 | parser + gates | baterias 42-46 | IMPLEMENTADO |
| 5 estados | §2 | — | — | ESPECIFICAÇÃO |
| contrato de 6 campos | §1 | CONTRACT parcial | — | PARCIAL |
| regra versionada | §4 | decisão existe, registry não | bordas Hoeffding | PARCIAL |
| recibo v1 completo | §5 + schema | hash sim, prévio não | — | PARCIAL |
| regras T1-T6 | §6 | T2/T3 parciais | — | ESPECIFICAÇÃO |
| verificador independente | §5 | verify_certificate (1 caso) | — | PARCIAL |

## 9. DECLARAÇÃO DE HONESTIDADE

Este documento NÃO declara que o ZYQL implementa tudo o que descreve. Ele congela o significado
dos termos para que implementação, teste e auditoria possam divergir dele de forma detectável.
O que está IMPLEMENTADO tem teste e recibo; o que está ESPECIFICAÇÃO é promessa com prazo, não fato.
