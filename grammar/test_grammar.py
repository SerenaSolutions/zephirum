# Validação mecânica da gramática ZYQL v1.3: parser + semântica T1/T2/T3 + normalização
import sys, math
from lark import Lark, exceptions, Tree, Token
G = Lark(open("zyql_v13.lark", encoding="utf-8").read(), parser="earley", lexer="dynamic", start="start")

def names(node): return [t.value for t in node.children if isinstance(t, Token) and t.type == "NAME"]

def semantica(tree):
    erros = []; medidos = set()
    def walk(n):
        for c in n.children:
            if isinstance(c, Tree):
                yield c
                yield from walk(c)
    for n in walk(tree):
        if n.data == "qubit_decl":
            kes = [c for c in n.children if isinstance(c, Tree) and c.data == "ket_expr"]
            if not kes: continue
            ke = kes[0]
            if ke.data == "ket_expr" and isinstance(ke.children[0], Tree) and ke.children[0].data == "superposition":
                sup = ke.children[0]
                kets = list(sup.find_data("ket")); norms = list(sup.find_data("normalizer"))
                nv = norms[0].children[0].value if norms else "?"
                alvo = math.sqrt(len(kets))
                if nv == "√2":
                    if len(kets) != 2: erros.append(f"T-norm: √2 exige 2 kets, há {len(kets)}")
                else:
                    try:
                        if abs(float(nv) - alvo) > 1e-9:
                            erros.append(f"T-norm: {len(kets)} kets exigem normalizador √{len(kets)}={alvo:.4f}, não {nv}")
                    except ValueError:
                        erros.append(f"T-norm: normalizador inválido {nv}")
        elif n.data == "medir":
            alvo = names(n)
            if alvo:
                if alvo[0] in medidos: erros.append(f"T3: '{alvo[0]}' já colapsado; medição dupla proibida")
                medidos.add(alvo[0])
        elif n.data == "evolution":
            l = [c for c in n.children if isinstance(c, Tree) and c.data == "lhs"]
            o = [c for c in n.children if isinstance(c, Tree) and c.data == "operand"]
            if l and o:
                ln, on = names(l[0]), names(o[0])
                if sorted(ln) != sorted(on):
                    erros.append(f"T2: evolução unitária exige lhs≡operand; obtido {ln} ← {on}")
                for q in on:
                    if q in medidos: erros.append(f"T3: '{q}' colapsado não pode evoluir")
    return erros

VALIDOS = [
 ("programa completo do kernel (mensagem do Diretor)", '''// ZYQL v1.3 — programa canônico
portão ⟨|⟩ "verificar correlação Bell":
qbit φ ← (|0⟩ + |1⟩)/√2
qbit a ← |0⟩
a, b ← CNOT × (a, b)
qif a: b ← X × b
bit m ← medir(a)
qbit ψ ← Ry(θ) × |0⟩
θ ← otimizar(esperança(H(ψ)))
→ 1 | 0 | REFUSED'''),
 ("bell mínimo", 'qbit a ← |0⟩\nqbit b ← |0⟩\na, b ← CNOT × (a, b)'),
 ("hadamard", 'qbit a ← |0⟩\na ← H × a'),
 ("paramétrico T5", 'qbit ψ ← Ry(0.75) × |0⟩'),
 ("decisão apenas recusa", 'portão ⟨|⟩ "propósito proibido":\n→ REFUSED'),
]
INVALIDOS_PARSE = [
 ("ket inválido", 'qbit a ← |2⟩'),
 ("colapso faltando ⟩", 'qbit a ← |0'),
 ("evolução sem operando", 'a ← H ×'),
 ("qif sem corpo", 'qif a:'),
 ("clonagem por gramática (T1 sintático)", 'qbit a ← |0⟩\nqbit b ← a'),
 ("portão sem decisão", 'portão ⟨|⟩ "p":\nqbit a ← |0⟩'),
 ("bit ligado a qbit", 'bit m ← a'),
]
INVALIDOS_SEM = [
 ("T2: reescrita não-unitária", 'qbit a ← |0⟩\nqbit b ← |0⟩\na ← H × b'),
 ("T3: uso após colapso", 'qbit a ← |0⟩\nbit m ← medir(a)\na ← H × a'),
 ("normalização errada", 'qbit a ← (|0⟩ + |1⟩)/3'),
]
fails = 0
for nome, src in VALIDOS:
    try:
        e = semantica(G.parse(src))
        print(f"VALIDO   {'PASS' if not e else 'FAIL '+str(e):4s} {nome}"); fails += 1 if e else 0
    except Exception as ex: print(f"VALIDO   FAIL  {nome}: {str(ex)[:90]}"); fails += 1
for nome, src in INVALIDOS_PARSE:
    try:
        G.parse(src); print(f"INVALIDO FAIL  {nome}: aceito indevidamente"); fails += 1
    except exceptions.UnexpectedInput: print(f"INVALIDO PASS  {nome}")
    except Exception as ex: print(f"INVALIDO FAIL  {nome}: {str(ex)[:90]}"); fails += 1
for nome, src in INVALIDOS_SEM:
    try:
        e = semantica(G.parse(src))
        print(f"SEMANT   {'PASS' if e else 'FAIL'}  {nome}" + (f": {e[0]}" if e else ": aceito indevidamente"))
        if not e: fails += 1
    except Exception as ex: print(f"SEMANT   FAIL  {nome}: {str(ex)[:90]}"); fails += 1
print(f"\nRESULTADO: {15-fails}/15 PASS" + ("" if fails==0 else f" | {fails} FALHAS"))
sys.exit(0 if fails==0 else 1)
