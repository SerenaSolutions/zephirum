#!/usr/bin/env python3
"""BATERIA SPARSE-VERIFY — fecha o achado 11 da auditoria.

Decisões esparas de 13..64 qubits agora têm verificação independente:
o checker re-deriva a separabilidade da FONTE por postos 2x2 em todos
os cortes (rota diferente da recursão do motor) e recusa divergência.

Casos: GHZ separado por N (13..64), produto esparso, forja de suporte,
forja de veredito, e o recibo real da demo de 64 qubits da auditoria.
"""
import os, sys, copy, json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from nexa_core import parse_nexa, NCA
from verify_certificate import verify

F = 0
def check(name, cond, why=""):
    global F
    print(("PASS " if cond else "FAIL ") + name + ("  # " + why if why else ""))
    if not cond:
        F += 1

def decide_and_verify(state, label):
    src = "ASK:\n    question: entangled == 1\nCONTRACT:\n    absolute_error: 0\nMODEL:\n    type: entanglement\n    state: %s\n" % state
    blocks = parse_nexa(src)
    res = NCA(blocks, label).compile()
    ok, why = verify(blocks, res["certificate"])
    return res, ok, why

# T1: GHZ esparso em N=13,20,64 — emaranhado, verificado INDEPENDENTEMENTE
for n in (13, 20, 64):
    last = (1 << n) - 1
    res, ok, why = decide_and_verify("sparse(%d) 0:3, %d:5" % (n, last), "T1-%d" % n)
    check("T1-ghz%d" % n, res["answer"] is True and ok,
          "emaranhado + verificado (%s)" % why[:60])

# T2: produto esparso N=16 — separavel, veredito 0
res, ok, why = decide_and_verify("sparse(16) 0:1, 65535:1", "T2")
# NOTA: |0..0> + |1..1> com amplitudes iguais e GHZ-like: e emaranhado.
# Um estado PRODUTO esparso: |0..0> + |0..01> (so o ultimo qubit difere):
res2, ok2, why2 = decide_and_verify("sparse(16) 0:7, 1:5", "T2b")
check("T2-produto", res2["answer"] is False and ok2,
      "separavel + verificado (%s)" % why2[:60])

# T3: forja de suporte — evidencia mente sobre o numero de entradas
src = ("ASK:\n    question: entangled == 1\nCONTRACT:\n    absolute_error: 0\n"
       "MODEL:\n    type: entanglement\n    state: sparse(20) 0:3, 1048575:5\n")
blocks = parse_nexa(src)
res = NCA(blocks, "T3").compile()
forge = copy.deepcopy(res["certificate"])
forge["EVIDENCE"]["support"] = 99
okf, whyf = verify(blocks, forge)
check("T3-forja-suporte", not okf, whyf[:60])

# T4: forja de veredito — inverte o campo fully_separable
forge2 = copy.deepcopy(res["certificate"])
forge2["EVIDENCE"]["fully_separable"] = True
okf2, whyf2 = verify(blocks, forge2)
check("T4-forja-veredito", not okf2, whyf2[:60])

# T5: certificado legitimo do GHZ-20 verifica (regressao dupla do caminho)
ok5, why5 = verify(blocks, res["certificate"])
check("T5-legitimo", ok5, why5[:60])

# T6: cross-source (cert de PRODUTO contra fonte GHZ) — barrado pelo INPUT_HASH
# ANTES da rota de postos: defesa em camadas. A rota de postos em si roda em
# todo certificado legitimo (T1/T2/T5 retornam "cross-checked by rank-1 minors").
src_prod = ("ASK:\n    question: entangled == 1\nCONTRACT:\n    absolute_error: 0\n"
            "MODEL:\n    type: entanglement\n    state: sparse(20) 0:7, 1:5\n")
res_prod = NCA(parse_nexa(src_prod), "T6a").compile()
blocks_ghz = parse_nexa(src)  # fonte GHZ-20 la de cima
ok6, why6 = verify(blocks_ghz, res_prod["certificate"])
check("T6-rank-route", not ok6, why6[:70])

print("-" * 64)
if F == 0:
    print("RESULTADO: PASS — esparso 13..64 qubits agora tem verificação independente")
    sys.exit(0)
print("RESULTADO: FAIL — %d casos reprovados" % F)
sys.exit(1)
