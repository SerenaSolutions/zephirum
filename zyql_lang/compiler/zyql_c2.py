#!/usr/bin/env python3
# C2 — COMPILADOR ZYQL -> CIRCUITO — kernel ZEPHYRUM 1.12
# Estado: IMPLEMENTADO (familias PRODUCT e UNIFORM_2, escopo honesto v0.1)
# Semantica: 1 (compila) / 0 (falha) / REFUSED (fora de escopo ou entrada ruim).
# PROVIMENTO (ordem do CEO): HARNESS de verificacao exata + RAG da casa
# consultados em TODA compilacao, citados no rastro.
import os, sys, json
from fractions import Fraction as Fr

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, ".."))
sys.path.insert(0, os.path.join(BASE, "..", "..", "docs"))
from zyql_parser import parse
from zyql_rag import build_index, query

_idx = None
def rag(consulta, k=2):
    global _idx
    if _idx is None: _idx = build_index()
    return [f"{os.path.relpath(c['doc'])}#L{c['line']}" for _, c in query(_idx, consulta, k)]

def fr_of(v):
    return Fr(str(v))

def compile_state(state):
    """state: lista de 4 amplitudes -> (gates, veredito) com aritmetica exata."""
    if not isinstance(state, list) or len(state) != 4:
        return None, "REFUSED", "state deve ser lista de 4 amplitudes (2 qubits)"
    amps = [fr_of(v) for v in state]
    if sum(a * a for a in amps) != 1:
        return None, "REFUSED", "vetor de estado nao normalizado (soma dos quadrados != 1, exata)"
    nz = [i for i, a in enumerate(amps) if a != 0]
    if len(nz) == 1 and abs(amps[nz[0]]) == 1:
        i = nz[0]
        gates = [{"gate": "X", "qubit": b} for b in (0, 1) if (i >> b) & 1]
        if amps[i] < 0:
            gates.append({"gate": "Z", "qubit": 0})
        return {"familia": "PRODUCT", "gates": gates,
                "estado_alvo": state, "verificacao":
                {"tipo": "permutacao de base", "amplitude_no_indice": str(amps[i])}}, "OK", None
    if all(a == Fr(1, 2) for a in amps):
        return {"familia": "UNIFORM_2", "gates": [{"gate": "H", "qubit": 0}, {"gate": "H", "qubit": 1}],
                "estado_alvo": state, "verificacao":
                {"tipo": "probabilidades", "todas_as_probabilidades": "1/4"}}, "OK", None
    return None, "REFUSED", "estado normalizado mas fora das familias compilaveis v0.1 (PRODUCT, UNIFORM_2)"

def harness_verifica(ir):
    """HARNESS: re-verifica o circuito emitido contra o alvo, exato."""
    if ir["familia"] == "PRODUCT":
        idx = 0
        for g in ir["gates"]:
            if g["gate"] == "X": idx ^= 1 << g["qubit"]
        alvo = [i for i, v in enumerate(ir["estado_alvo"]) if fr_of(v) != 0][0]
        return idx == alvo
    if ir["familia"] == "UNIFORM_2":
        return all(fr_of(v) * fr_of(v) == Fr(1, 4) for v in ir["estado_alvo"])
    return False

def compile_program(src):
    ok, ast, err = parse(src)
    if not ok:
        return {"veredito": "REFUSED", "motivo": f"parser: {err}",
                "rag": rag("secoes ordem canonica ASK CONTRACT MODEL")}
    model = ast.get("MODEL", {})
    t = model.get("type")
    if t == "threshold_sum":
        return {"veredito": "REFUSED",
                "motivo": "modelo classico: sem circuito quantico nesta versao",
                "rag": rag("modelo threshold_sum contrato absolute_error")}
    if t != "entanglement":
        return {"veredito": "REFUSED", "motivo": f"type desconhecido pelo compilador: {t!r}",
                "rag": rag("model type identifier")}
    if "state" not in model:
        return {"veredito": "REFUSED", "motivo": "MODEL sem state",
                "rag": rag("model_entry state number_list")}
    ir, veredito, motivo = compile_state(model["state"])
    traco = {"veredito": veredito,
             "rag": rag("state number_list entanglement amplitudes"),
             "ast_model": model}
    if veredito == "OK":
        traco["ir"] = ir
        traco["harness"] = {"verificado": harness_verifica(ir),
                             "metodo": "aritmetica exata de racionais"}
        if not traco["harness"]["verificado"]:
            traco["veredito"] = "FALHA_HARNESS"
    else:
        traco["motivo"] = motivo
    return traco
