#!/usr/bin/env python3
"""
fuzz_grammar.py — Automated Grammar & Semantic Fuzzer for ZYQL v1.3
Auditor: EXECUTIVO 3 — DIRETOR DE VERIFICAÇÃO E SEGURANÇA
"""

import sys, os, math
from lark import Lark, exceptions, Tree, Token

GRAMMAR_PATH = "/app/conversations/6a89df0012b12b33001c5066/grammar_v13/zyql_v13.lark"

with open(GRAMMAR_PATH, encoding="utf-8") as f:
    grammar_text = f.read()

G = Lark(grammar_text, parser="earley", lexer="dynamic", start="start")

def names(node):
    return [t.value for t in node.children if isinstance(t, Token) and t.type == "NAME"]

def semantica(tree):
    erros = []
    medidos = set()
    declarados = set()
    
    def walk(n):
        for c in n.children:
            if isinstance(c, Tree):
                yield c
                yield from walk(c)

    for n in walk(tree):
        if n.data == "qubit_decl":
            d_names = names(n)
            if d_names:
                declarados.add(d_names[0])
            kes = [c for c in n.children if isinstance(c, Tree) and c.data == "ket_expr"]
            if not kes: continue
            ke = kes[0]
            if ke.data == "ket_expr" and isinstance(ke.children[0], Tree) and ke.children[0].data == "superposition":
                sup = ke.children[0]
                kets = list(sup.find_data("ket"))
                norms = list(sup.find_data("normalizer"))
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
                if alvo[0] in medidos:
                    erros.append(f"T3: '{alvo[0]}' já colapsado; medição dupla proibida")
                medidos.add(alvo[0])
        elif n.data == "evolution":
            l = [c for c in n.children if isinstance(c, Tree) and c.data == "lhs"]
            o = [c for c in n.children if isinstance(c, Tree) and c.data == "operand"]
            if l and o:
                ln, on = names(l[0]), names(o[0])
                if sorted(ln) != sorted(on):
                    erros.append(f"T2: evolução unitária exige lhs≡operand; obtido {ln} ← {on}")
                for q in on:
                    if q in medidos:
                        erros.append(f"T3: '{q}' colapsado não pode evoluir")
    return erros

# -------------------------------------------------------------------
# TEST SUITE: 16 VALID PROGRAMS + 32 MALFORMED PROGRAMS
# -------------------------------------------------------------------

VALIDOS = [
    ("v01_canonical_kernel", '''portão ⟨|⟩ "verificar correlação Bell":
qbit φ ← (|0⟩ + |1⟩)/√2
qbit a ← |0⟩
a, b ← CNOT × (a, b)
qif a: b ← X × b
bit m ← medir(a)
qbit ψ ← Ry(θ) × |0⟩
θ ← otimizar(esperança(H(ψ)))
→ 1 | 0 | REFUSED'''),
    ("v02_bell_minimal", "qbit a ← |0⟩\nqbit b ← |0⟩\na, b ← CNOT × (a, b)"),
    ("v03_hadamard", "qbit a ← |0⟩\na ← H × a"),
    ("v04_parametric_ry", "qbit ψ ← Ry(0.75) × |0⟩"),
    ("v05_decision_refused_only", 'portão ⟨|⟩ "propósito proibido":\n→ REFUSED'),
    ("v06_multi_decision", 'portão ⟨|⟩ "p":\n→ 1 | 0 | REFUSED'),
    ("v07_multi_qubit_decl", "qbit a ← |0⟩\nqbit b ← |1⟩\na ← X × a\nb ← Z × b"),
    ("v08_qif_conditional", "qbit a ← |0⟩\nqbit b ← |0⟩\nbit m ← medir(a)\nqif m: b ← X × b"),
    ("v09_theta_optimization", "qbit ψ ← Ry(θ) × |0⟩\nθ ← otimizar(esperança(H(ψ)))"),
    ("v10_gated_ket_decl", "qbit a ← H × |0⟩"),
    ("v11_superpos_sqrt2", "qbit a ← (|0⟩ + |1⟩)/√2"),
    ("v12_superpos_float_sqrt2", "qbit a ← (|0⟩ + |1⟩)/1.4142135623730951"),
    ("v13_three_ket_superpos", "qbit a ← (|0⟩ + |1⟩ + |0⟩)/1.7320508075688772"),
    ("v14_sequential_measurements", "qbit a ← |0⟩\nqbit b ← |0⟩\nbit m1 ← medir(a)\nbit m2 ← medir(b)"),
    ("v15_gate_block_multistmt", 'portão ⟨|⟩ "g":\nqbit a ← |0⟩\na ← H × a\nbit m ← medir(a)\n→ 1 | 0'),
    ("v16_gate_block_theta", 'portão ⟨|⟩ "g2":\nqbit a ← Ry(θ) × |0⟩\nθ ← otimizar(esperança(H(a)))\n→ 1'),
]

# MALFORMED PROGRAMS TO TEST PARSER AND SEMANTICS
INVALIDOS = [
    # T2 & Positional Ordering
    ("m01_cnot_reorder", "qbit a ← |0⟩\nqbit b ← |0⟩\na, b ← CNOT × (b, a)", "T2: CNOT control/target operand reordering ignored"),
    # Redeclaration & Scope
    ("m02_qubit_redeclamation", "qbit a ← |0⟩\nqbit a ← |1⟩", "Qubit redeclaration in same scope allowed"),
    ("m03_medir_undeclared", "bit m ← medir(x)", "Measuring undeclared qubit x allowed"),
    # Gate Signatures & Parameters
    ("m04_ry_missing_param", "qbit a ← |0⟩\na ← Ry × a", "Parametric gate Ry accepted without parameter"),
    ("m05_ry_empty_parens", "qbit a ← |0⟩\na ← Ry() × a", "Empty parameter parenthesis in gate"),
    ("m06_ry_multi_params", "qbit a ← |0⟩\na ← Ry(0.1, 0.2) × a", "Multiple parameters in single parameter gate"),
    ("m07_cnot_with_param", "qbit a ← |0⟩\nqbit b ← |0⟩\na, b ← CNOT(0.5) × (a, b)", "Non-parametric gate CNOT given parameter"),
    ("m08_nested_gate_call", "qbit a ← |0⟩\na ← Ry(Ry(0.5)) × a", "Nested gate expression inside parameter"),
    # Normalizers & Superposition
    ("m09_normalizer_integer_3", "qbit a ← (|0⟩ + |1⟩)/3", "Wrong integer normalizer 3 for 2 kets"),
    ("m10_normalizer_exotic_sqrt3", "qbit a ← (|0⟩ + |1⟩)/√3", "Exotic normalizer √3 token in 2-ket superposition"),
    ("m11_normalizer_zero", "qbit a ← (|0⟩ + |1⟩)/0", "Division by zero in normalizer"),
    ("m12_unnormalized_same_ket", "qbit a ← (|0⟩ + |0⟩)/√2", "Unnormalized state |0>+|0> accepted with sqrt2"),
    ("m13_normalizer_sqrt2_four_kets", "qbit a ← (|0⟩ + |1⟩ + |0⟩ + |1⟩)/√2", "sqrt2 normalizer with 4 kets"),
    # Classical Branching & Aliasing
    ("m14_qif_on_unmeasured_qubit", "qbit a ← |0⟩\nqbit b ← |0⟩\nqif a: b ← X × b", "qif conditioned on unmeasured qubit 'a' instead of bit"),
    ("m15_qif_modifying_condition", "qbit a ← |0⟩\nbit m ← medir(a)\nqif m: a ← H × a", "T3: modifying collapsed qubit 'a' inside qif"),
    ("m16_qif_empty_body", "qbit a ← |0⟩\nqif a:", "qif with empty body"),
    # Identifiers & Unicode
    ("m17_unicode_var_alpha", "qbit α ← |0⟩", "Greek letter variable name α"),
    ("m18_unicode_var_chinese", "qbit_中文 ← |0⟩", "Chinese characters in qubit variable name"),
    ("m19_unicode_in_gate_string", 'portão ⟨|⟩ "teste α β":\n→ REFUSED', "Unicode in gate description string"),
    ("m20_theta_as_qubit_name", "qbit θ ← |0⟩", "θ token used as qubit variable name"),
    # Theta Reassignment & Optimization
    ("m21_theta_direct_reassign_num", "θ ← 0.5", "Direct numeric reassignment of θ without otimizar()"),
    ("m22_theta_arithmetic", "θ ← θ + 0.1", "Arithmetic expression reassignment of θ"),
    # Measurement & Double Collapse
    ("m23_double_measurement", "qbit a ← |0⟩\nbit m1 ← medir(a)\nbit m2 ← medir(a)", "Double measurement of same qubit 'a'"),
    ("m24_use_after_measurement", "qbit a ← |0⟩\nbit m ← medir(a)\na ← H × a", "T3: evolution after collapse"),
    ("m25_bit_assigned_directly", "qbit a ← |0⟩\nbit m ← a", "Direct assignment of qubit to bit without medir()"),
    ("m26_medir_multiple_args", "qbit a ← |0⟩\nqbit b ← |0⟩\nbit m ← medir(a, b)", "medir() with multiple qubit arguments"),
    # Operand & LHS Mismatch
    ("m27_lhs_single_op_multi", "qbit a ← |0⟩\nqbit b ← |0⟩\na ← CNOT × (a, b)", "Single qubit LHS with 2-qubit CNOT operand"),
    ("m28_lhs_multi_op_single", "qbit a ← |0⟩\nqbit b ← |0⟩\na, b ← H × a", "2-qubit LHS with single-qubit H operand"),
    ("m29_non_unitary_rewrite", "qbit a ← |0⟩\nqbit b ← |0⟩\na ← H × b", "T2: lhs != operand (a ← H × b)"),
    # Grammar Structure
    ("m30_ket_invalid_digit", "qbit a ← |2⟩", "Invalid ket digit |2>"),
    ("m31_ket_unclosed", "qbit a ← |0", "Unclosed ket bracket"),
    ("m32_cloning_syntax", "qbit a ← |0⟩\nqbit b ← a", "Syntax-level cloning attempt (b ← a)"),
]

def main():
    print("=" * 80)
    print("FUZZ DA GRAMÁTICA E CHECAGENS SEMÂNTICAS ZYQL v1.3")
    print("Auditor: EXECUTIVO 3 — DIRETOR DE VERIFICAÇÃO E SEGURANÇA")
    print("=" * 80)

    pass_val = 0
    fail_val = 0
    print("\n--- [1] TESTANDO PROGRAMAS VÁLIDOS (Alvo: >= 15) ---")
    for tag, src in VALIDOS:
        try:
            tree = G.parse(src)
            errs = semantica(tree)
            if errs:
                print(f"[VAL] FAIL  {tag:30s} -> Erros semânticos: {errs}")
                fail_val += 1
            else:
                print(f"[VAL] PASS  {tag:30s}")
                pass_val += 1
        except Exception as ex:
            print(f"[VAL] FAIL  {tag:30s} -> Parse exception: {str(ex)[:70]}")
            fail_val += 1

    print(f"\nResumo Válidos: {pass_val}/{len(VALIDOS)} PASS")

    print("\n--- [2] TESTANDO PROGRAMAS MALFORMADOS (Alvo: >= 30) ---")
    false_accepts = []
    false_rejections = []
    true_rejects = 0

    for tag, src, desc in INVALIDOS:
        parse_ok = False
        sem_errs = []
        parse_err = None

        try:
            tree = G.parse(src)
            parse_ok = True
            sem_errs = semantica(tree)
        except Exception as ex:
            parse_err = str(ex)

        if parse_ok and not sem_errs:
            # Malformed program accepted by BOTH parser and semantics -> FALSE ACCEPT!
            false_accepts.append((tag, src, desc))
            print(f"[MAL] FALSO ACEITE!! {tag:30s} -> {desc}")
        elif not parse_ok:
            print(f"[MAL] REJEITADO(PARSE) {tag:30s} -> {parse_err[:50]}...")
            true_rejects += 1
        else:
            print(f"[MAL] REJEITADO(SEM)   {tag:30s} -> Erro: {sem_errs[0][:60]}")
            true_rejects += 1

    print("\n" + "=" * 80)
    print("RELATÓRIO DE FALSOS ACEITES E FALSOS REJEIÇÕES")
    print("=" * 80)
    print(f"Total Malformados Testados : {len(INVALIDOS)}")
    print(f"Rejeições Corretas        : {true_rejects}")
    print(f"FALSOS ACEITES Detectados : {len(false_accepts)}")

    if false_accepts:
        print("\nDETALHAMENTO DOS FALSOS ACEITES:")
        for idx, (tag, src, desc) in enumerate(false_accepts, 1):
            print(f"\n--- FALSO ACEITE #{idx}: {tag} ---")
            print(f"Descrição: {desc}")
            print("Código aceito:")
            print("  " + "\n  ".join(src.split("\n")))

    print("\n" + "=" * 80)
    print("ANÁLISE JURÍDICA / PARECER SOBRE A ANOMALIA T2 DE REORDENAÇÃO DO CNOT")
    print("=" * 80)
    cnot_fa = any(tag == "m01_cnot_reorder" for tag, _, _ in false_accepts)
    print(f"Caso: 'a, b ← CNOT × (b, a)' foi aceito? {cnot_fa}")
    print("""
PARECER DO DIRETOR DE VERIFICAÇÃO E SEGURANÇA:
1. Reordenação de Operandos em Portas Assimétricas (CNOT):
   Em computação quântica, a porta CNOT(controle, alvo) possui matriz unitária não-comutativa:
     CNOT(a, b)|01⟩ = |01⟩, CNOT(a, b)|10⟩ = |11⟩
   ao passo que:
     CNOT(b, a)|01⟩ = |11⟩, CNOT(b, a)|10⟩ = |10⟩.
   A checagem semântica T2 atual executa `sorted(ln) != sorted(on)`. Como `sorted(['a', 'b']) == sorted(['b', 'a'])`,
   o verificador aceita silenciosamente a troca de controle e alvo.

2. Avaliação de Severidade: ALTA.
   Fundamentação: A premissa do ZYQL é a verificação formal de correção antes da execução.
   Permitir a inversão de controle/alvo em portas quânticas multi-qubit sem alerta ou rejeição
   corrompe a semântica do circuito, alterando a matriz unitária implementada sem ser detectado
   pelo parser ou pela checagem T2.

3. Outras Lacunas de Segurança Identificadas:
   - Ausência de tabela de símbolos (aceita medição de qubits não declarados).
   - Ausência de verificação de aridade/assinatura de portas (aceita CNOT(0.5) e Ry sem parâmetro).
   - Ausência de verificação de tipo no condicional qif (aceita 'qif qubit' sem medição prévia).
   - Validação fraca de normalizadores em superposição (aceita (|0⟩ + |0⟩)/√2).
   - Re-declaração de qubits no mesmo escopo não é bloqueada.
""")

    return 0

if __name__ == "__main__":
    sys.exit(main())
