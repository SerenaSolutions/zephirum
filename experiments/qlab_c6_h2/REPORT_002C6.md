# QLAB-002 · C6 — RELATÓRIO FINAL
## H₂ ponta a ponta em ZYQL: programa .zeph compilado e executado em QPU física (ibm_fez), com tripartição local↔simulado↔hardware
Data: 12-13/10/2026 · Jobs reais: db6k5e4lf4us73c5gglg (estágio 1) e db6kassvf2bc73d1ca0g (estágio 2) · 61.440 tiros totais, dentro dos orçamentos pré-registrados.

**Este é o C6 das coordenadas:** o primeiro PROGRAMA .zeph completo da linguagem (não primitivas isoladas) compilado pelo pipeline kernel C→QASM3→QPU e corrido em silício físico, com recibo em cadeia (certs SHA-256 de pré-registro antes da coleta, ambos os estágios).

## O PROGRAMA (h2.zeph, hash d7e15bfe…)
Portão ⟨|⟩ com propósito declarado; ansatz de duas configurações |HF⟩⊕|duplamente excitado⟩ via Ry(θ)+3 CNOT; θ←otimizar(esperança(H(a))); decisão trivalente 1|0|REFUSED. Parseia na gramática congelada v1.3 com semântica limpa (A1 PASS, bateria 15/15).

## PROCEDÊNCIA DO HAMILTONIANO (computado, não citado)
pennylane.qchem.molecular_hamiltonian, H₂ STO-3G, R=0.735 Å, Jordan-Wigner: 15 termos, 4 qubits. Diagonalização exata local: E0(FCI) = −1.1361891625 Ha. Matriz salva (qlab_c6_H.npy) — reproduzível por qualquer auditor.

## CRITÉRIOS PRÉ-REGISTRADOS × RESULTADO
| critério | resultado | veredito |
|---|---|---|
| A1 .zeph na gramática v1.3 | parse + semântica limpos, 15/15 | PASS |
| A2 prova de compilação | fidelidade do estado preparado vs analítico = 1.000000000000 (kernel→QASM3→qiskit) | PASS |
| A3 ansatz exato | min E local −1.136145 Ha vs FCI −1.136189 Ha (gap 4,45e−05 Ha) | PASS |
| A4 concordância 3σ vs banda Aer | estágio 1: 13/30 · estágio 2: 16/30 | PARCIAL — desvio sistemático |
| A5 \|E_hw−E0\| ≤ 0,20 Ha | 0,2066 Ha (sem mitigação de erro) | FAIL por 0,007 |
| A6 recomputação independente | igualdade exata (duas regras de contagem) | PASS |
| A7 forma da curva na região do mínimo | mínimo hardware em θ=6,1276, região central da grade | PASS |
| A8 relatório com desvio declarado | esta seção | PASS |

## TRIPARTIÇÃO: E(θ) em Ha (grade final de 12 pontos)
Estágio 1 (grade uniforme): θ/π = 0.000: ex −1.1173 / hw −0.8965 · 0.333: −0.5419/−0.3960 · 0.667: +0.2990/+0.2269 · 1.000: +0.5645/+0.4636 · 1.333: −0.0110/−0.0230 · 1.667: −0.8519/−0.7045
Estágio 2 (região do mínimo, proposta pelo otimizador de fit):
| θ | exato | hardware | σ |
|---|---|---|---|
| 5.8876 | −1.121383 | −0.908491 | 0.0113 |
| 5.9676 | −1.131377 | −0.918268 | 0.0110 |
| 6.0476 | −1.135902 | −0.911276 | 0.0110 |
| 6.1276 | −1.134929 | −0.929539 | 0.0105 |
| 6.2076 | −1.128465 | −0.907037 | 0.0108 |
| 6.3476 | −1.104083 | −0.915163 | 0.0102 |

VQE hardware (sem mitigação): E = −0.9295 ± 0.0105 Ha em θ = 6.1276 rad. FCI: −1.136189 Ha. Desvio: 0.2066 Ha.

## ACHADOS HONESTOS
1. *O pipeline ponta a ponta funciona*: linguagem congelada → kernel C → QASM3 → transpile → QPU → contagens → energia, com recibo e pré-registro em ambos os estágios. Esse é o resultado principal do C6.
2. *A forma da curva é capturada, a profundidade não*: o hardware encontra o mínimo na região certa (deslocado de um ponto de grade, dentro do σ), mas as amplitudes estão amortecidas ~80% — a energia de correlação mede 0.03 Ha em hardware vs 0.019 Ha exato, e a distância ao FCI é dominada por ruído estocástico por pulso (consistente com FRONTIER 003: o erro rastreia pulsos, não duração; este circuito tem ~30 pulsos físicos por ramo de medida).
3. *O modelo calibrado da Aer subestima o ruído real* (A4 29/60): mesma direção das missões FRONTIER 001-003. O modelo não substitui medição.
4. *Lição de desenho* (corrigida em voo com emenda pré-registrada): grade uniforme de 6 pontos errou a região do mínimo; o otimizador clássico de modelo (fit A+B·cosθ+C·sinθ) localizou a região corretamente e o estágio 2 a amostrou.
5. *Próximo passo natural* (não executado): mitigação de erro (ZNE ou reamostragem por termo) para fechar o gap de 0.2 Ha; e leitura do recibo com a decisão trivalente (REFUSED se p̂ indistinguível de ambíguo).

## ARTEFATOS
h2.zeph+cert · prereg_002c6.json+cert · prereg_002c6_estagio2.json+cert · circuitos_002c6{,_s2}.json · refs_002c6{,_s2}.json · cert_002c6{,_s2}.json · hw_002c6{,_s2}.json · verify_002c6{,_s2}.json · f_c6.py · f_c6_s2.py · f_c6_verify{,_s2}.py · qlab_c6_H.npy · jobs db6k5e4lf4us73c5gglg / db6kassvf2bc73d1ca0g
