# C3 — TEOREMA DE UNIVERSALIDADE ZYQL

Estado: VERIFICADO (enumeracao exata + prova algebrica) · Kernel de referencia: ZEPHYRUM 1.12
Recibo: RECEIPT_C3.json (hash 55121a60)

## Resultado central (FATO)

O conjunto de portas atual do kernel — {H, X, Y, Z, CNOT} — **nao e universal**.

Prova por enumeracao exata (aritmetica em Z[i][sqrt2][1/2], sem ponto flutuante):

1. n=1: |<H,X,Z>| = 16 elementos (fecho finito).
2. n=2: a imagem projetiva de <H1,H2,CNOT> tem 72 elementos em Sp(4,2) — o espaco
   simpletico completo tem 720. Logo o conjunto atual gera um subgrupo ESTRITO,
   dez vezes menor que o grupo de Clifford.
3. Grupo finito => existe distancia minima positiva a qualquer unitaria fora dele:
   nao ha aproximacao, nem exata nem aproximada.

## Lema (T nao e Clifford) — prova algebrica exata

T X T+ = (X + Y)/sqrt2, verificado em aritmetica exata. Esse resultado NAO e
fase x Pauli (entradas (1 -/+ i)/sqrt2 nao pertencem a {0, +-1, +-i}).
Como um elemento de Clifford deve levar Pauli em fase x Pauli, T nao pertence ao
grupo de Clifford.

## Teorema 2 (Clifford nao basta) — citado

Mesmo com S adicionado (|<H,X,Z,S>| = 192 = 8 fases x 24), o grupo de Clifford e
finito e classicamente simulavel em tempo polinomial (Gottesman-Knill 1998).
Universalidade exigiria BQP = P. Portanto Clifford nao e universal.

## Teorema 3 (universalidade com T) — citado + evidencia numerica

<H, T, CNOT> e denso em SU(2^n) (Boykin-Mor-Pulver-Rowell 2000; Shi 2002;
Aharonov 2003), com aproximacao epsilon por O(log^c(1/epsilon)) portas
(Solovay-Kitaev 1997).

Evidencia numerica (NUMERICA, nao prova): busca aleatoria em <H,T> mostra erro
mediano de aproximacao caindo com o comprimento da palavra:
10 geradores -> 0,398 | 20 -> 0,215 | 30 -> 0,189 | 40 -> 0,156.

## Corolario para a linguagem (o que muda de fato)

Para o ZYQL ser universal, o kernel e o compilador C2 precisam de uma porta
nao-Clifford. Especificacao da extensao:

1. kernel: adicionar T (pi/8) e Rz(theta) com aritmetica exata onde possivel;
2. compilador C2: nova familia ROTATION com sintese ZYZ exata para 1 qubit;
3. recibos: registrar a familia e a profundidade; sem isso a universalidade nao
   pode ser alegada.

## Rotulos AUŠRA

- Ordens de grupo: FATO (enumeracao exata).
- T nao-Clifford: FATO (prova algebrica exata).
- Teoremas 2 e 3: INFERENCIA (literatura citada, nao reprovada aqui).
- Densidade: NUMERICA (evidencia).
- Universalidade da ZYQL hoje: NAO (veredito verdadeiro e informativo).
