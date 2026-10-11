# ZYQL-QUANTUM FRONTIER 003 — RELATÓRIO FINAL
## Discriminação causal: acoplamento por duração (H2) vs erro estocástico por pulso (H4) · ibm_fez

Data: 11/10/2026 · Pré-registro: hypotheses_003.json (10ff6d15…) e design_003.json (b12a9cd7…), hash antes da coleta. Job real: db5qqb4lf4us73c4e5v0 (6 circuitos × 2048 = 12.288 tiros, espera 15,6 s). Orçamento pré-registrado respeitado (16.000 máx).

**Nova capacidade de kernel:** este é o primeiro experimento do mundo, até onde sabemos, em que a primitiva exigida pela análise de active learning da missão anterior foi implementada (IR v4: `zyql_ir_delay`) e usada para quebrar um confound declarado. Sequência completa da orquestração: 002 declara inseparabilidade H2/H4 → especificação demanda `delay` → implementação + regressão byte-a-byte → 003 discrimina.

## EMPARELHAMENTO DE DURAÇÃO (medido no backend, não assumido)
dt = 4,000 ns · bell = 444 dt · hh8 = 540 dt · delay_full = bell + 96 dt = 540 dt EXATOS.
HH8: 35 pulsos, 540 dt. Delay_full: 3 pulsos, 540 dt. Mesma duração, 32 pulsos de diferença — o desenho isola duração de pulso pela primeira vez nesta série.

## RESULTADOS (2048 tiros por circuito, job único)

| circuito | ZZ hardware | IC 95% | pulsos | duração | banda modelo |
|---|---|---|---|---|---|
| bell_base | +0,9600 | [+0,947, +0,972] | 3 | 444dt | [+0,973, +0,984] |
| hh8 | +0,9072 | [+0,889, +0,925] | 35 | 540dt | [+0,962, +0,966] |
| delay_full | +0,9492 | [+0,935, +0,962] | 3 | 540dt | [+0,970, +0,979] |
| delay_half | +0,9473 | [+0,934, +0,960] | 3 | 492dt | [+0,972, +0,981] |
| bell_149 | +0,8926 | [+0,873, +0,912] | 3 | 444dt | [+0,838, +0,852] |
| delay_149 | +0,8604 | [+0,839, +0,882] | 3 | 540dt | [+0,831, +0,846] |

## DECISÃO PELA REGRA PRÉ-REGISTRADA
z(delay_full vs bell_base) = −1,15 → |z| < 2,58: delay retém o Bell (diferença não significativa).
z(delay_full vs hh8) = +3,61 → z > 2,58: delay é SIGNIFICATIVAMENTE acima do HH8 na MESMA duração.

**VEREDITO: H4 (erro estocástico por pulso) CONFIRMADA. H2 (acoplamento por duração) REFUTADA na forma pré-registrada.** Na duração emparelhada (540 dt), 3 pulsos retêm ZZ=+0,949 contra +0,907 com 35 pulsos. O decaimento com profundidade rastreia a contagem de pulsos, não o tempo de circuito.

Secundárias: delay_half ≈ bell (z=−1,35), consistente com H4 (sem monotonicidade com duração). Replicação no par (149,148): delay_149 abaixo de bell_149 com z=−2,14 — abaixo do limiar pré-registrado (2,58), reportada como observação residual honesta: possível efeito fraco de ociosidade no par de pior calibração, não conclusivo nesta potência.

## CADEIA CAUSAL COMPLETA (001→002→003)
1. 001: decaimento de ZZ com profundidade é real; controle produto mostra viés migrante.
2. 002: não é erro coerente-estático (eco refuta), não é leitura correlacionada (matriz refuta); modelo por pulso prevê retido; confound pulsos×duração declarado.
3. 003: não é duração (delay emparelhado refuta). **O mecanismo dominante do decaimento é erro estocástico por pulso físico.**

Classificação: categoria B consolidada (mecanismo instrumental demonstrado por discriminação experimental, em três missões encadeadas, com pré-registro, replicação de par e limites declarados). Nenhuma anomalia; nenhuma alegação de nova física. O que foi demonstrado é o método: a máquina identificou o experimento que faltava, a linguagem ganhou a primitiva, e o veredito saiu da regra escrita antes da coleta.

## Limitações
1. D=384 ns é curto frente a T1 (~centenas de µs): H2 na forma de relaxação térmica estaria abaixo da detecção; o que foi refutado é acoplamento com efeito mensurável nessa escala de duração. Durações 10-100× maiores exigiriam orçamento maior de tiros.
2. Observação residual no par (149,148) (z=−2,14) não alcança significância; próximo experimento informativo: delay longos (10× D) nesse par específico.
3. Uma época de calibração; deriva entre épocas já documentada em 002.

## Artefatos
hypotheses_003.json+cert · design_003.json+cert · circuits_003.json · refs_003.json · cert_003.json · hw3.json · verify_003.json · q3_*.qasm3 · f3.py · f3_verify.py · Job: db5qqb4lf4us73c4e5v0
