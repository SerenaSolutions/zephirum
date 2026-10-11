# ZYQL — WHITE PAPER DE AUDITORIA (v1.0, 11/10/2026)

*Documento documental para auditoria técnica independente. Toda a sintaxe da linguagem e os algoritmos, com trilha de evidência verificável.*

![Logo ZYQL](../assets/brand/logo_zyql_betta_oficial_11out2026.jpg)

**ZEPHIRUM/ZYQL** — o sistema tem duas camadas com papéis distintos e auditáveis:

1. **Camada de decisão exata (ZCA)** — o compilador da necessidade: prova que nenhuma computação é necessária e só executa o que resta, com certificado verificável (CERT_HASH) e verificador independente. Decisões trivalentes 1/0/Z (REFUSED). Documentada em `docs/PHASE_3.md` e no `README.md`.
2. **Camada quântica (kernel ZYQL)** — o núcleo de semântica quântica em C (`zyql.h`, libzyql v0.1.0, IR v3) que formula, prova, despacha e verifica circuitos em hardware real IBM Quantum. É o objeto principal deste white paper, com evidência desta camada obtida em ibm_fez e ibm_marrakesh (recibos: `results/*.json`, QPU ledger em `results/qpu_ledger.md`).

Convenção de honestidade: [PROVADO] foi demonstrado em hardware/testes reais e é reproduzível; [ESPECIFICADO] é projeto formal ainda não implementado no binário.

---

## 1. GRAMÁTICA COMPLETA DA LINGUAGEM

### 1.1 Camada quântica — primitivas do kernel (ZYQL v0.3/v0.4)

| Primitiva | Sintaxe | Semântica formal |
|---|---|---|
| SUPERPOSE | `SUPERPOSE nome: \|a1> "t1" \|a2> "t2" ...` | \|ψ⟩ = Σᵢαᵢ\|ramoᵢ⟩; Σ\|αᵢ|²=1 forçado (E_ARG se degradada) |
| MEASURE | `MEASURE nome` | P(i)=\|αᵢ|² (regra de Born); colapso irreversível |
| ENTANGLE | `ENTANGLE a b` | correlação não-local; medir uma determina a outra |
| DECOHERE | `DECOHERE ruido` | decoerência paramétrica, mistura com ruído ∈ [0,1] |
| NOCLONE | `NOCLONE` | teorema da não-clonagem como política: segredos são irreplicáveis (E_NOCLONE) |
| QUBIT/CLONE | `QUBIT nome` / `CLONE nome` | alocação; CLONE de qubit protegido é bloqueado |
| PROVE | `PROVE bell` | verificação programática do Bell no kernel (ver §4, escopo) |
| KEYGEN/SEAL/OPEN | `KEYGEN bb84 [eve]` `SEAL chave dados` `OPEN chave dados` | QSD BB84 com detecção de Eva por QBER (E_EVE) + selo OTP |
| MOUNT/LSDEV | `MOUNT /dev/qpuX GRANTED` | montagem autorizada; E_NOGRANT sem outorga |
| QPU | `QPU circuito` | despacho: exige prova + outorga + hashes + orçamento NA MESMA SESSÃO (E_NOPROOF) |
| TRACE | `TRACE` | log auditável imutável de todas as operações |
| EXT | `EXT nasa \| agents` | extensões em QUARENTENA DECLARADA; nunca importação silenciosa |

### 1.2 Camada de agentes (v0.1, origem documentada em 10 repositórios)

```
AGENT nome GOAL "..." [TOOLS a,b] [MEMORY n]
PLAN nome: p1 -> p2 -> p3
TOOL/USE ferramenta "arg" [IN base]
RAG nome FROM "doc1" "doc2" | RAG nome FROM NASA neo|apod|donki
MEMORY / REMEMBER "texto" / RECALL "consulta"
CREW nome = a1,a2,a3 TASK "..."
REFLECT nome ON "saída" CRITERIA "c1","c2"
GUARD BLOCK|FLAG /regex/ "mensagem"     # barra segredos ANTES de executar a linha
```

NASA é EXT, não núcleo. O runtime não embute LLM (gancho aberto) e não fabrica dado: sem token, o QPU cai para simulador e diz isso.

## 2. C API COMPLETA (zyql.h — libzyql v0.1.0, ABI estável, 25 funções)

Ciclo de vida: `zyql_new(seed)`, `zyql_free`, `zyql_version`
Núcleo quântico: `zyql_superpose`, `zyql_measure`, `zyql_entangle`, `zyql_collapsed`, `zyql_decohere`
Segurança: `zyql_noclone_rule`, `zyql_guard_text`, `zyql_qubit_alloc/clone/measure`, `zyql_prove_bell`, `zyql_mount`, `zyql_dispatch_allowed`, `zyql_bb84`, `zyql_seal`, `zyql_open`
IR v3: `zyql_ir_reset/h/x/cnot/rx/rz/rzz/measure/qasm3`, `zyql_prove_claim`
Auditoria: `zyql_trace_count`, `zyql_trace_get`

Códigos de erro (contrato ABI): `0 OK · -1 E_ARG · -2 E_FULL · -3 E_NOVAR · -4 E_NOCLONE · -5 E_LINEAR · -6 E_PROOF · -7 E_NOMOUNT · -8 E_NOGRANT · -9 E_NOPROOF · -10 E_EVE · -11 E_NOKEY`

## 3. O ALGORITMO — PIPELINE DO KERNEL

```
PROVE → ASSESS → CERTIFY → EXECUTE → VERIFY
PROVE    verificação matemática na MESMA sessão (estado por instância; claims de
         outra sessão não valem — E_NOPROOF [PROVADO 2×]). Controles equivalentes:
         ‖U_emitido − U_referência‖∞ ≤ 1e−9 sobre o QASM gerado.
ASSESS   viabilidade: qubits, profundidade, pulsos, orçamento Σ tiros ≤ B,
         poder 1−β, limite de detecção δmin = z₁₋α·σ₀·√(2/n).
CERTIFY  cadeia Merkle de hashes dos artefatos ANTES da coleta; reverificada no
         despacho. Pré-registro de hipóteses com hash (anti HARKing).
EXECUTE  portões: prova + outorga + hashes + orçamento. Caminho único:
         IR → OpenQASM 3 → Qiskit → transpile nível 0 → backend autorizado.
         Job id persistido ANTES da extração.
VERIFY   recálculo dos brutos com fórmulas independentes; incerteza declarada;
         resultados negativos preservados.
```

## 4. ESCOPO DO PROVE (declaração honesta)

`zyql_prove_bell` deriva o Bell com constantes literais: é asserção programática, não provador geral [PROVADO em auditoria]. A prova matemática do MAX-CUT e das identidades de circuito é feita no pipeline, FORA do kernel, com dupla verificação independente. `zyql_prove_claim` é atestação externa registrada no TRACE — bookkeeping auditável, nunca prova por si. Nenhuma dessas funções é vendida aqui como o que não é.

## 5. CIÊNCIA ATIVA [ESPECIFICADO — matemática validada com dados reais]

```
EIG(E) = E_{y∼p̄}[KL(π(·|y,E)‖π)] = I(hipótese; Y_E)   (identidade de cobertura)
E* = argmax_E EIG(E)/custo(E)
Regra anti-confound: se todo E deixa par vivo com d_TV ≤ ε, o kernel emite
o desenho que quebra o empate (ex.: primitiva delay do IR v4 para separar
pulsos de duração). REFUTE com Holm-Bonferroni; COMMIT em categorias A–E;
promoção de categoria SOMENTE com replicação independente.
```

Demonstração com dados reais (FRONTIER 002, M=8000, σ de 2048 tiros): EIG inicial HH8=0,614 · MATRIZ=0,197 · ECO=0,102 · VIRTUAL8=0,000 nats; após refutação do erro coerente: HH8=0,378 · MATRIZ=0,237. O algoritmo reproduz a análise manual e identifica o confound pulsos×duração. Números completos: `docs/PAPER_zephirum.md` e arquivos da missão (§7).

## 6. TRILHA DE EVIDÊNCIA PARA AUDITORIA INDEPENDENTE

| Evento | Identificador real | Verificado |
|---|---|---|
| Bell Φ+ hardware | db450d84qg6s73c1lcm0 (ibm_fez), ⟨ZZ⟩=+0,874, ⟨XX⟩=+0,905 | emaranhamento confirmado |
| Bell via C API | db5p3r2mb58s738aqncg, ZZ=+0,8164 | recalculado dos brutos |
| MAX-CUT QAOA (QLAB-001) | db5pmeamb58s738arbv0; ótimo 14; ideal 11,196 / ruído 11,080 / hardware 11,044 | certificado clássico duplo |
| FRONTIER 001 | db5q8eqmb58s738as2rg + db5q8fclf4us73c4der0; H1 temporal refutada (N=1024, z máx 0,78) | pré-registro 3269495c…/4e48f785… |
| FRONTIER 002 | db5qev04qg6s73c3rlm0 (fez) + db5qfj4lf4us73c4dprg (marrakesh); 3 hipóteses refutadas por controle; previsão em retido erro 0,0024 | pré-registro 91e4752e…/610c3cb1… |
| Regressões IR v2/v3 | Bell byte-a-byte idêntico; unidades E/R/V identidade exata 1e−9 | sem quebra de ABI |
| Testes de falha | 12/12 (circuito inválido, grafo malformado, adulteração pós-certificação, E_NOGRANT, E_NOPROOF, orçamento…) | security por recusa |
| Camada ZCA | 500.000 problemas, 0 respostas erradas, 500.000/500.000 certificados verificados, 20/20 forjados rejeitados | stress_results_5000.json |

## 7. REPRODUÇÃO PELO AUDITOR

```
gcc -O2 -fPIC -shared -o libzyql.so zyql_c_api.c -lm     # núcleo (c-api/)
python3 prototype/run_tests.py                           # soundness da camada exata
python3 prototype/stress_test.py 500000                 # bateria estressante
python3 prototype/verifier_indep/test_verificador_c.py  # verificador C independente
# camada quântica (requer API_KEY IBM no ambiente):
python3 qlab/qlab.py classical && prove && assess && optimize && execute-hw && verify
python3 frontier/f2.py prove && build && refs && execute && python3 frontier/f2_verify.py
```

Credenciais ficam no ambiente, nunca no código. Cada job id acima pode ser conferido no serviço IBM pelo auditor com acesso ao projeto.

## 8. HISTÓRICO DE VERSÕES

| Versão | Mudança |
|---|---|
| zyql v0.1 | linguagem declarativa de agentes; 10 primitivas; origem em 10 repositórios documentada |
| zyql v0.3 | núcleo de semântica quântica pura; NASA/agentes em EXT (quarentena); GUARD/FLAG; NOCLONE |
| libzyql v0.1.0 · IR v1 | C API, ABI estável, 11 códigos de erro; Bell em hardware real |
| IR v2 | rx/rz/rzz + prove_claim (QAOA end-to-end via kernel) |
| IR v3 | porta x (sequências de eco); regressão byte-a-byte mantida |
| zyql v0.4 [ESPECIFICADO] | primitivas epistêmicas HYPOTHESIS/PREDICT/SELECT/REFUTE/COMMIT; seleção ativa por EIG; IR v4 com delay; Holm no núcleo |

*Declaração final de honestidade: nada neste documento promete funcionalidade não testada. Até esta data o sistema produziu três refutações, duas previsões confirmadas em dados retidos, 500 mil decisões exatas verificadas e zero alegação de nova física.*

— Emitido por Solene (agent) sob direção do CEO, 11/10/2026. Marca oficial: betta ciano (decisão do CEO, 11/10/2026).
