#!/usr/bin/env python3
"""
zyqlc.py — Compilador ZYQL v1.3 → OpenQASM 3.0
Serena Solutions — Projeto ZEPHIRUM/ZYQL
Cargo: EXECUTIVO 2 — DIRETOR DE ENGENHARIA (Implementação)

Responsabilidade:
  Lê um programa ZYQL (.zeph ou string) → Realiza parse com zyql_v13.lark (Earley/Dynamic)
  → Executa checagens semânticas T1-T6 → Gera OpenQASM 3.0 válido e legível.

Mapeamento de Construtos ZYQL → OpenQASM 3.0:
  - Declaração qbit → qubit[nq] q; e preparação inicial (X se |1⟩, H para (|0⟩+|1⟩)/√2)
  - Porta H → h q[i];
  - Porta X → x q[i];
  - Porta CNOT → cx q[c], q[t];
  - Porta Ry(θ) / Ry(val) → ry(val) q[i];
  - Porta Rx(θ) / Rx(val) → rx(val) q[i];
  - Porta Rz(θ) / Rz(val) → rz(val) q[i];
  - Porta Rzz(θ) → cx q[c], q[t]; rz(θ) q[t]; cx q[c], q[t]; (decomposição stdgates.inc)
  - Condicional qif → cx q[controle], q[alvo];
  - Medição medir → m[i] = measure q[i]; e bit[nq] m;
  - Superposição literal (|0⟩+|1⟩)/√2 → decomposição em Hadamard (h)
  - Parâmetro θ simbólico → input float θ;
  - Otimização VQE → Marcada como intenção em comentários QASM
"""

import sys
import os
import argparse
import math
from lark import Lark, Tree, Token, exceptions

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_LARK_PATH = os.path.join(BASE_DIR, "grammar_v13", "zyql_v13.lark")


class SemanticError(Exception):
    """Erro de validação semântica das regras T1-T6."""
    pass


def extract_names(node):
    """Extrai todos os identificadores NAME de um nó ou subárvore Lark."""
    res = []
    if isinstance(node, Token):
        if node.type == "NAME":
            res.append(node.value)
    elif isinstance(node, Tree):
        for child in node.children:
            res.extend(extract_names(child))
    return res


def extract_param_value(gate_node):
    """
    Extrai o valor e tipo de parâmetro de um nó 'gate'.
    Ex.: gate -> [Token('NAME', 'Ry'), Tree('gate_param', [Token('NUMBER', '0.75')])]
    """
    for child in gate_node.children:
        if isinstance(child, Tree) and child.data == "gate_param":
            if child.children:
                sub = child.children[0]
                if isinstance(sub, Token):
                    return sub.value, sub.type
                elif isinstance(sub, Tree):
                    tok = sub.children[0]
                    return tok.value, getattr(tok, "type", None)
        elif isinstance(child, Token) and child.type == "gate_param":
            return child.value, "gate_param"
    return None, None


def validate_semantics(tree):
    """
    Validação semântica T1-T6 (reaproveitada e expandida de test_grammar.py):
    - T-norm: superposição (ket1 + ket2)/norm exige normalizador correto (ex.: √2 para 2 kets).
    - T2: evolução unitária exige lhs ≡ operand (multiconjunto).
    - T3: uso de qubit colapsado após medir ou medição dupla é proibido.
    """
    errors = []
    medidos = set()

    def walk(n):
        if isinstance(n, Tree):
            yield n
            for c in n.children:
                yield from walk(c)

    for n in walk(tree):
        if n.data == "qubit_decl":
            kes = [c for c in n.children if isinstance(c, Tree) and c.data == "ket_expr"]
            if not kes:
                continue
            ke = kes[0]
            if ke.data == "ket_expr" and isinstance(ke.children[0], Tree) and ke.children[0].data == "superposition":
                sup = ke.children[0]
                kets = list(sup.find_data("ket"))
                norms = list(sup.find_data("normalizer"))
                nv = norms[0].children[0].value if norms and norms[0].children else "?"
                alvo = math.sqrt(len(kets))
                if nv == "√2":
                    if len(kets) != 2:
                        errors.append(f"T-norm: √2 exige 2 kets, há {len(kets)}")
                else:
                    try:
                        if abs(float(nv) - alvo) > 1e-9:
                            errors.append(f"T-norm: {len(kets)} kets exigem normalizador √{len(kets)}={alvo:.4f}, não {nv}")
                    except ValueError:
                        errors.append(f"T-norm: normalizador inválido {nv}")

        elif n.data == "medir":
            alvo = extract_names(n)
            if alvo:
                if alvo[0] in medidos:
                    errors.append(f"T3: '{alvo[0]}' já colapsado; medição dupla proibida")
                medidos.add(alvo[0])

        elif n.data == "evolution":
            l = [c for c in n.children if isinstance(c, Tree) and c.data == "lhs"]
            o = [c for c in n.children if isinstance(c, Tree) and c.data == "operand"]
            if l and o:
                ln, on = extract_names(l[0]), extract_names(o[0])
                if sorted(ln) != sorted(on):
                    errors.append(f"T2: evolução unitária exige lhs≡operand; obtido {ln} ← {on}")
                for q in on:
                    if q in medidos:
                        errors.append(f"T3: '{q}' colapsado não pode evoluir")

    return errors


class ZYQLCompiler:
    """Compilador ZYQL → OpenQASM 3.0."""

    def __init__(self, lark_path=None):
        path = lark_path or DEFAULT_LARK_PATH
        if not os.path.exists(path):
            raise FileNotFoundError(f"Arquivo de gramática ZYQL não encontrado: {path}")
        with open(path, "r", encoding="utf-8") as f:
            grammar_content = f.read()
        self.parser = Lark(grammar_content, parser="earley", lexer="dynamic", start="start")

    def compile(self, source_code):
        """Compila código ZYQL para OpenQASM 3.0."""
        try:
            tree = self.parser.parse(source_code)
        except exceptions.LarkError as e:
            raise SyntaxError(f"Erro de Parse ZYQL: {e}")

        sem_errors = validate_semantics(tree)
        if sem_errors:
            raise SemanticError("; ".join(sem_errors))

        return self._generate_qasm3(tree)

    def _generate_qasm3(self, tree):
        qubit_map = {}
        next_qubit_idx = 0
        inputs = set()
        instructions = []
        comments = []

        def get_qubit(name):
            nonlocal next_qubit_idx
            if name not in qubit_map:
                qubit_map[name] = next_qubit_idx
                next_qubit_idx += 1
            return qubit_map[name]

        def process_gate(gate_node, target_idx, ctrl_idx=None):
            gate_name = gate_node.children[0].value
            param_val, param_type = extract_param_value(gate_node)
            if param_val == "θ" or param_type == "THETA":
                inputs.add("θ")

            g_upper = gate_name.upper()
            if ctrl_idx is not None:
                if g_upper == "X" or gate_name == "cx":
                    instructions.append(f"cx q[{ctrl_idx}], q[{target_idx}];")
                else:
                    p_str = f"({param_val})" if param_val else ""
                    instructions.append(f"c{gate_name.lower()}{p_str} q[{ctrl_idx}], q[{target_idx}];")
            else:
                if g_upper == "H":
                    instructions.append(f"h q[{target_idx}];")
                elif g_upper == "X":
                    instructions.append(f"x q[{target_idx}];")
                elif g_upper.startswith("RY"):
                    p_str = param_val if param_val else "0"
                    instructions.append(f"ry({p_str}) q[{target_idx}];")
                elif g_upper.startswith("RX"):
                    p_str = param_val if param_val else "0"
                    instructions.append(f"rx({p_str}) q[{target_idx}];")
                elif g_upper.startswith("RZ"):
                    p_str = param_val if param_val else "0"
                    instructions.append(f"rz({p_str}) q[{target_idx}];")
                else:
                    p_str = f"({param_val})" if param_val else ""
                    instructions.append(f"{gate_name.lower()}{p_str} q[{target_idx}];")

        def process_node(node):
            if not isinstance(node, Tree):
                return

            if node.data == "gate_block":
                str_toks = [t for t in node.children if isinstance(t, Token) and t.type == "STRING"]
                if str_toks:
                    comments.append(f"// portão {str_toks[0].value}")
                for child in node.children:
                    process_node(child)

            elif node.data == "qubit_decl":
                name_tok = [t for t in node.children if isinstance(t, Token) and t.type == "NAME"][0]
                q_name = name_tok.value
                idx = get_qubit(q_name)

                ke_node = [c for c in node.children if isinstance(c, Tree) and c.data == "ket_expr"][0]
                first_c = ke_node.children[0]

                if first_c.data == "ket":
                    bit_toks = [t for t in first_c.children if isinstance(t, Token) and t.type == "BIT"]
                    if bit_toks and bit_toks[0].value == "1":
                        instructions.append(f"x q[{idx}];")
                elif first_c.data == "gated_ket":
                    gate_node = [c for c in first_c.children if isinstance(c, Tree) and c.data == "gate"][0]
                    ket_node = [c for c in first_c.children if isinstance(c, Tree) and c.data == "ket"][0]
                    bit_toks = [t for t in ket_node.children if isinstance(t, Token) and t.type == "BIT"]
                    if bit_toks and bit_toks[0].value == "1":
                        instructions.append(f"x q[{idx}];")
                    process_gate(gate_node, idx)
                elif first_c.data == "superposition":
                    # (|0⟩ + |1⟩)/√2 -> Decomposição em Hadamard (H)
                    instructions.append(f"h q[{idx}];")

            elif node.data == "evolution":
                l_node = [c for c in node.children if isinstance(c, Tree) and c.data == "lhs"][0]
                o_node = [c for c in node.children if isinstance(c, Tree) and c.data == "operand"][0]
                g_node = [c for c in node.children if isinstance(c, Tree) and c.data == "gate"][0]

                op_names = extract_names(o_node)
                g_name = g_node.children[0].value
                p_val, p_type = extract_param_value(g_node)
                if p_val == "θ" or p_type == "THETA":
                    inputs.add("θ")

                if len(op_names) == 1:
                    idx = get_qubit(op_names[0])
                    process_gate(g_node, idx)
                elif len(op_names) == 2:
                    idx0 = get_qubit(op_names[0])
                    idx1 = get_qubit(op_names[1])
                    if g_name.upper() == "CNOT":
                        instructions.append(f"cx q[{idx0}], q[{idx1}];")
                    elif g_name.upper().startswith("RZZ"):
                        # rzz(a,b,θ) = cx(a,b) rz(θ,b) cx(a,b) — stdgates.inc não tem rzz nativo
                        p_str = p_val if p_val else "0"
                        instructions.append(f"cx q[{idx0}], q[{idx1}];")
                        instructions.append(f"rz({p_str}) q[{idx1}];")
                        instructions.append(f"cx q[{idx0}], q[{idx1}];")
                    else:
                        p_str = f"({p_val})" if p_val else ""
                        instructions.append(f"{g_name.lower()}{p_str} q[{idx0}], q[{idx1}];")

            elif node.data == "branching":
                names = [t.value for t in node.children if isinstance(t, Token) and t.type == "NAME"]
                ctrl_name = names[0]
                ctrl_idx = get_qubit(ctrl_name)

                evol_node = [c for c in node.children if isinstance(c, Tree) and c.data == "evolution"][0]
                o_node = [c for c in evol_node.children if isinstance(c, Tree) and c.data == "operand"][0]
                g_node = [c for c in evol_node.children if isinstance(c, Tree) and c.data == "gate"][0]

                op_names = extract_names(o_node)
                target_idx = get_qubit(op_names[0])
                process_gate(g_node, target_idx, ctrl_idx=ctrl_idx)

            elif node.data == "medir":
                q_names = extract_names(node)
                if q_names:
                    q_idx = get_qubit(q_names[0])
                    instructions.append(f"m[{q_idx}] = measure q[{q_idx}];")

            elif node.data == "optimization":
                inputs.add("θ")
                comments.append("// Intenção VQE: θ ← otimizar(esperança(...))")

            elif node.data == "decision":
                ditems = []
                for c in node.children:
                    if isinstance(c, Tree) and c.data == "ditem":
                        for sub in c.children:
                            if isinstance(sub, Token):
                                ditems.append(sub.value)
                if ditems:
                    comments.append(f"// Decisão: → {' | '.join(ditems)}")

            else:
                for child in node.children:
                    process_node(child)

        process_node(tree)

        lines = ["OPENQASM 3.0;", 'include "stdgates.inc";']
        if comments:
            lines.extend(comments)
        for inp in sorted(inputs):
            lines.append(f"input float {inp};")

        nq = max(next_qubit_idx, 0)
        if nq > 0:
            lines.append(f"qubit[{nq}] q;")
            lines.append(f"bit[{nq}] m;")

        lines.extend(instructions)
        return "\n".join(lines) + "\n"


def compile_zyql(source_code, lark_path=None):
    """Função utilitária de conveniência."""
    compiler = ZYQLCompiler(lark_path=lark_path)
    return compiler.compile(source_code)


def main():
    parser = argparse.ArgumentParser(description="Compilador ZYQL → OpenQASM 3.0")
    parser.add_argument("input_file", nargs="?", help="Caminho do arquivo .zeph")
    parser.add_argument("-o", "--output", help="Caminho do arquivo OpenQASM 3.0 de saída")
    parser.add_argument("-c", "--code", help="Código ZYQL inline para compilação")
    args = parser.parse_args()

    if args.code:
        src = args.code
    elif args.input_file:
        with open(args.input_file, "r", encoding="utf-8") as f:
            src = f.read()
    else:
        src = sys.stdin.read()

    try:
        qasm = compile_zyql(src)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(qasm)
            print(f"OpenQASM 3.0 gerado com sucesso em {args.output}")
        else:
            sys.stdout.write(qasm)
    except Exception as e:
        sys.stderr.write(f"ERRO DE COMPILAÇÃO: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
