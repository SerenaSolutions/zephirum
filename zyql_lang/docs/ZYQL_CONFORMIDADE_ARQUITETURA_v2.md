# ZYQL — MATRIZ DE CONFORMIDADE: ARQUITETURA v2 x CÓDIGO REAL
Kernel: ZEPHYRUM 1.12 · Data: 2026-10-12 · Emissor: executivo técnico
Estados da casa: IMPLEMENTADO / EXPERIMENTAL / ESPECIFICAÇÃO / BLOQUEADO
Linha: requisito → especificação → código → teste → evidência → estado

## 1. Contrato central (entrada, propósito, critério, política, evidência, veredito)

| Requisito | Código real | Estado |
| contrato com entrada/propósito | sephirum/prototype/example.zeph (ASK/MODEL), decision_kernel.py | PARCIAL: seções ASK/CONTRACT/MODEL existem e são parseadas |
| critério matemático explícito | parser: predicado com comparadores; example.zeph.cert.json | PARCIAL: predicado simples, sem regras versionadas |
| política autorizada antes de executar | authority.json existe apenas no SO híbrido (zephyrum_hybrid_os/), NÃO no pipeline da linguagem | ESPECIFICAÇÃO |
| evidência para auditoria | recibos selados por hash em toda bateria | IMPLEMENTADO (hash sha256 em cada recibo) |
| veredito com significado documentado | semântica 1/0/REFUSED no parser e nas baterias | IMPLEMENTADO para 3 estados; 5 estados = ESPECIFICAÇÃO |

## 2. Semântica de vereditos

| 1 / 0 / REFUSED | zyql_parser.py + bateria C1 (101/101, 12/12 recusas) | IMPLEMENTADO (recibo 118d3f1b) |
| INCONCLUSIVE | 0 ocorrências no código | ESPECIFICAÇÃO (decisão do CEO 2026-10-12) |
| ERROR (falha técnica distinta de recusa) | 0 ocorrências; baterias distinguem informalmente | ESPECIFICAÇÃO |
| separação estado-de-execução vs veredito-científico | parcial: receipts têm status (CONCLUIDO/NAO CONCLUIDO) separado do veredito AUŠRA | PARCIAL, formalizar no M1 |

## 3. Gramática e sintaxe

| EBNF v1.0 (ISO/IEC 14977) + parser provado | sephirum/docs/ZYQL_EBNF_v1.0.md + zyql_parser.py | IMPLEMENTADO |
| Sintaxe v2 proposta (programa/versão, entrada, contrato exige, critério, execução, decisão, certificação) | não existe no parser | ESPECIFICAÇÃO (congelar no M1) |
| literais Dirac | parser aceita ket/bra, 5/5 provados | IMPLEMENTADO |
| análise estática de tipos e contratos impossíveis | inexistente | ESPECIFICAÇÃO (M2) |

## 4. Operações do núcleo

| contract (pré/pós-condições, invariantes) | seção CONTRACT existe (absolute_error); condições gerais não | PARCIAL → ESPECIFICAÇÃO |
| authorize (política/permissão pré-execução) | inexistente no runtime da linguagem | ESPECIFICAÇÃO |
| evaluate (regra identificada e versionada) | decision_kernel.py tem rungs/métodos não versionados | PARCIAL → ESPECIFICAÇÃO (registro de regras) |
| attest (recibo vincula execução↔evidências) | cada bateria emite recibo com hash; recibo PRÉVIO inexistente | PARCIAL → ESPECIFICAÇÃO (recibo prévio) |
| verify_receipt (verificação independente) | verify_certificate.py existe para o fluxo threshold_sum; ferramenta geral zyql-verify inexistente | PARCIAL → ESPECIFICAÇÃO |

## 5. Recibo

| campos de identidade (receipt_version, program_hash, language_version, compiler_version, policy_version) | recibos têm kernel + RECEIPT_HASH; versionamento formal ausente | PARCIAL |
| campos de execução (execution_id, input_commitment, environment, backend, start/end) | backend, inicio/fim UTC, job_id presentes no recibo HW | PARCIAL |
| evidências e decisão (evidence_hashes, decision_rule, verdict, uncertainty, limitations) | veredito AUŠRA presente; uncertainty/limitations não padronizados | PARCIAL |
| cadeia (previous_receipt_hash) | 0 ocorrências | ESPECIFICAÇÃO |
| assinatura ML-DSA-44 (FIPS 204) | pq_receipt.py + pq_keys/ + integrity_sign.py; recibos de hardware assinados | IMPLEMENTADO (assinatura em recibos QPU) |
| schema público verificável sem o emissor | inexistente como padrão único | ESPECIFICAÇÃO |

## 6. Fluxo de execução e isolamento

| parse + validação com recusa | zyql_parser 1/0/REFUSED | IMPLEMENTADO |
| recusa ANTES da execução por política | inexistente no pipeline | ESPECIFICAÇÃO |
| recibo prévio assinado | inexistente | ESPECIFICAÇÃO |
| ambiente controlado/limites de recurso | não aplicado por mecanismo de SO/sandbox | ESPECIFICAÇÃO (ordem do CEO: zero-I/O precisa de mecanismo concreto, não configuração) |
| zero-I/O do kernel C | verificado por inspeção de símbolos na lib compilada (EXEC-2, conformidade v0.3) | IMPLEMENTADO para o kernel; para runtime geral = ESPECIFICAÇÃO |

## 7. Matemática e incerteza

| Hoeffding formalizada com hipóteses e bordas | sephirum/prototype/hoeffding/hoeffding_formal.py (57 config, 0 violações) | IMPLEMENTADO (recibo 88c52ccf) |
| subsistema de decisão com regra/hipóteses/limites registrados | formalização existe isolada; não integrada como regra versionada da linguagem | PARCIAL → ESPECIFICAÇÃO |
| decisão sobre inconclusão estatística → INCONCLUSIVE | inexistente | ESPECIFICAÇÃO |
| política de múltiplos testes | inexistente | ESPECIFICAÇÃO |

## 8. Verificação independente

| verificação de hashes/assinaturas | test_integrity.py, test_pqprotect.py, test_trust.py (baterias de falsificação 200/2000) | IMPLEMENTADO como testes |
| validação de esquema e cadeia de recibos | inexistente (sem cadeia) | ESPECIFICAÇÃO |
| recálculo do veredito sem executar o programa | verify_certificate.py faz isso PARA O CASO threshold_sum | EXPERIMENTAL (um caso) |
| relatório de afirmações verificadas vs confiança externa | rótulos AUŠRA cumprem papel informal | PARCIAL → formalizar |
| 4 níveis (integridade/autenticidade/reprodutibilidade/correção) | prática da casa separa informalmente | ESPECIFICAÇÃO (formalizar) |

## 9. Marcos

| M1 fundação (semântica 5 estados, gramática, contratos, formato de recibo) | EBNF v1.0 feito; o restante é ESPECIFICAÇÃO a congelar | EM CURSO (C1 feito) |
| M2 compilador (parser + análise estática) | parser feito e provado; análise estática não | EM CURSO |
| M3 execução (runtime determinístico clássico) | decision_kernel/nexa_core como protótipos | EXPERIMENTAL |
| M4 confiança (assinatura + verificador independente) | ML-DSA IMPLEMENTADO; zyql-verify geral ESPECIFICAÇÃO | PARCIAL |
| M5 ciência (motor de vereditos + backend quântico) | baterias exatas (42/43/44) + primitivas em QPU física (recibo 5ad265b7) | EXPERIMENTAL |
