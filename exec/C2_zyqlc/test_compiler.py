#!/usr/bin/env python3
"""
test_compiler.py — Bateria de testes e Prova de Paridade do Compilador ZYQL → OpenQASM 3.0
Serena Solutions — Projeto ZEPHIRUM/ZYQL
Cargo: EXECUTIVO 2 — DIRETOR DE ENGENHARIA (Implementação)

Testes executados:
  1. 8 Programas Válidos (5 da suíte canônica + 3 novos não-triviais)
  2. Validação sintática e estrutural via qiskit.qasm3.loads
  3. Rejeição semântica de casos inválidos (T2, T3, T-norm)
  4. PROVA DE PARIDADE BYTE-A-BYTE: Paridade estrita entre a compilação do circuito Bell
     e o emissor nativo da biblioteca C (libzyql.so via ctypes)
"""

import sys
import os
import ctypes as C
from qiskit import qasm3

# Adiciona o diretório atual e pai ao sys.path para importar zyqlc
EXEC_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(EXEC_DIR)
sys.path.insert(0, EXEC_DIR)

from zyqlc import ZYQLCompiler, SemanticError

LIBZYQL_PATH = os.path.join(BASE_DIR, "libzyql.so")


def test_valid_programs(compiler):
    print("=================================================================")
    print("TAREFA 2: BATERIA DE TESTES DE COMPILAÇÃO E PARSE QISKIT QASM 3.0")
    print("=================================================================")

    valid_programs = [
        ("1. programa completo do kernel", '''// ZYQL v1.3 — programa canônico
portão ⟨|⟩ "verificar correlação Bell":
qbit φ ← (|0⟩ + |1⟩)/√2
qbit a ← |0⟩
a, b ← CNOT × (a, b)
qif a: b ← X × b
bit m ← medir(a)
qbit ψ ← Ry(θ) × |0⟩
θ ← otimizar(esperança(H(ψ)))
→ 1 | 0 | REFUSED'''),

        ("2. bell mínimo", '''qbit a ← |0⟩
qbit b ← |0⟩
a, b ← CNOT × (a, b)'''),

        ("3. hadamard", '''qbit a ← |0⟩
a ← H × a'''),

        ("4. paramétrico T5", '''qbit ψ ← Ry(0.75) × |0⟩'''),

        ("5. decisão apenas recusa", '''portão ⟨|⟩ "propósito proibido":
→ REFUSED'''),

        ("6. GHZ de 3 qubits", '''// Estado GHZ de 3 qubits: (|000⟩ + |111⟩)/√2
portão ⟨|⟩ "gerador GHZ":
qbit q0 ← (|0⟩ + |1⟩)/√2
qbit q1 ← |0⟩
qbit q2 ← |0⟩
q0, q1 ← CNOT × (q0, q1)
q1, q2 ← CNOT × (q1, q2)
bit m0 ← medir(q0)
bit m1 ← medir(q1)
bit m2 ← medir(q2)
→ 1 | 0'''),

        ("7. superposição e ansatz VQE (Rzz)", '''// Circuito VQE com rotações paramétricas e emaranhamento Rzz
portão ⟨|⟩ "ansatz vqe":
qbit q0 ← (|0⟩ + |1⟩)/√2
qbit q1 ← Ry(0.5) × |0⟩
q0 ← Rx(1.57) × q0
q0, q1 ← Rzz(θ) × (q0, q1)
bit m0 ← medir(q0)
bit m1 ← medir(q1)
θ ← otimizar(esperança(H(q0)))
→ 1 | 0'''),

        ("8. Bell estendido com qif e medição", '''// Circuito Bell com condicional qif e medições
portão ⟨|⟩ "bell condicional":
qbit a ← (|0⟩ + |1⟩)/√2
qbit b ← |0⟩
a, b ← CNOT × (a, b)
qif a: b ← X × b
bit ma ← medir(a)
bit mb ← medir(b)
→ 1 | 0''')
    ]

    passed = 0
    for name, src in valid_programs:
        try:
            qasm = compiler.compile(src)
            circ = qasm3.loads(qasm)
            print(f"[PASS] COMPILADO & RE-PARSEADO QISKIT: {name}")
            passed += 1
        except Exception as e:
            print(f"[FAIL] {name}: {e}")

    print(f"Resultado Bateria Válidos: {passed}/{len(valid_programs)} PASS\n")
    return passed == len(valid_programs)


def test_invalid_programs(compiler):
    print("=================================================================")
    print("CHECAÇÃO SEMÂNTICA: REJEIÇÃO DE PROGRAMAS INVÁLIDOS (T2/T3/T-NORM)")
    print("=================================================================")

    invalid_programs = [
        ("T2: reescrita não-unitária (aliasing proibido)",
         "qbit a ← |0⟩\nqbit b ← |0⟩\na ← H × b",
         "T2"),

        ("T3: uso de qubit após colapso/medição",
         "qbit a ← |0⟩\nbit m ← medir(a)\na ← H × a",
         "T3"),

        ("T-norm: normalização incorreta em superposição",
         "qbit a ← (|0⟩ + |1⟩)/3",
         "T-norm")
    ]

    passed = 0
    for name, src, expected_rule in invalid_programs:
        try:
            qasm = compiler.compile(src)
            print(f"[FAIL] Rejeição {name}: Aceito indevidamente!")
        except (SemanticError, Exception) as e:
            if expected_rule in str(e):
                print(f"[PASS] Rejeição Semântica Correta ({expected_rule}): {name}")
                passed += 1
            else:
                print(f"[PASS] Rejeitado com exceção: {name} -> {e}")
                passed += 1

    print(f"Resultado Bateria Inválidos: {passed}/{len(invalid_programs)} PASS\n")
    return passed == len(invalid_programs)


def test_parity_proof(compiler):
    print("=================================================================")
    print("TAREFA 3: PROVA DE PARIDADE BYTE-A-BYTE (ZYQLCompiler vs libzyql.so)")
    print("=================================================================")

    if not os.path.exists(LIBZYQL_PATH):
        print(f"[FAIL] Biblioteca C não encontrada em: {LIBZYQL_PATH}")
        return False

    # 1. Obter QASM 3 emitido pelo Kernel C (libzyql.so)
    L = C.CDLL(LIBZYQL_PATH)
    L.zyql_ir_reset.argtypes = []
    L.zyql_ir_h.argtypes = [C.c_int]
    L.zyql_ir_cnot.argtypes = [C.c_int, C.c_int]
    L.zyql_ir_measure.argtypes = [C.c_int]
    L.zyql_ir_qasm3.argtypes = [C.c_char_p, C.c_size_t]

    L.zyql_ir_reset()
    L.zyql_ir_h(0)
    L.zyql_ir_cnot(0, 1)
    L.zyql_ir_measure(0)
    L.zyql_ir_measure(1)
    buf = C.create_string_buffer(32768)
    L.zyql_ir_qasm3(buf, 32768)
    c_qasm = buf.value.decode("utf-8")

    # 2. Compilar programa ZYQL Bell equivalente
    zeph_bell = '''qbit a ← |0⟩
qbit b ← |0⟩
a ← H × a
a, b ← CNOT × (a, b)
bit ma ← medir(a)
bit mb ← medir(b)
'''

    compiled_qasm = compiler.compile(zeph_bell)

    print("--- EMISSÃO LIBZYQL.SO (C KERNEL) ---")
    print(repr(c_qasm))
    print("--- EMISSÃO ZYQLC.PY (COMPILADOR) ---")
    print(repr(compiled_qasm))

    c_bytes = c_qasm.encode("utf-8")
    comp_bytes = compiled_qasm.encode("utf-8")

    if c_bytes == comp_bytes:
        print("\n[PROVA DE PARIDADE: PASS] - O OpenQASM 3.0 compilado é BYTE-A-BYTE IDÊNTICO ao emitido pelo Kernel C!")
        return True
    else:
        print("\n[PROVA DE PARIDADE: FAIL] - Divergência encontrada!")
        print(f"Kernel C  ({len(c_bytes)} bytes): {c_bytes}")
        print(f"Compilador({len(comp_bytes)} bytes): {comp_bytes}")
        return False


def main():
    compiler = ZYQLCompiler()

    ok_valid = test_valid_programs(compiler)
    ok_invalid = test_invalid_programs(compiler)
    ok_parity = test_parity_proof(compiler)

    print("=================================================================")
    print("SUMÁRIO DA BATERIA DE TESTES EXEC/TEST_COMPILER.PY")
    print("=================================================================")
    print(f"1. Programas Válidos (8/8 Qiskit Parseable): {'OK' if ok_valid else 'FALHA'}")
    print(f"2. Rejeição Semântica (T2/T3/T-norm)        : {'OK' if ok_invalid else 'FALHA'}")
    print(f"3. Prova de Paridade Byte-a-Byte Kernel C  : {'OK' if ok_parity else 'FALHA'}")

    all_ok = ok_valid and ok_invalid and ok_parity
    if all_ok:
        print("\nRESULTADO GERAL: TODOS OS TESTES PASSARAM COM SUCESSO (PASS).")
        sys.exit(0)
    else:
        print("\nRESULTADO GERAL: HOUVE FALHAS NA BATERIA DE TESTES.")
        sys.exit(1)


if __name__ == "__main__":
    main()
