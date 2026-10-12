#!/usr/bin/env python3
# RAG LOCAL DA CASA — kernel ZEPHYRUM 1.12
# Índice offline sobre os documentos da linguagem; recuperação por tokens
# (BM25-lite). Zero rede, zero segredo: tudo dos próprios documentos da casa.
import re, math, os

def _docs():
    base = os.path.dirname(os.path.abspath(__file__))
    return [os.path.join(base, "..", "docs", "ZYQL_EBNF_v1.0.md"),
            os.path.join(base, "..", "docs", "ZEPHIRUM_STANDARD_v0.3.md")]

def build_index():
    idx = []
    for doc in _docs():
        p = os.path.normpath(doc)
        if not os.path.exists(p): continue
        for n, line in enumerate(open(p), 1):
            if line.strip():
                idx.append({"doc": p, "line": n, "text": line.strip()})
    return idx

def _toks(s):
    return set(re.findall(r"[a-z0-9_]+", s.lower()))

def query(idx, text, k=3):
    qt = _toks(text)
    scored = []
    for c in idx:
        inter = len(qt & _toks(c["text"]))
        if inter:
            scored.append((inter / (1 + math.log(1 + len(_toks(c["text"])))), c))
    scored.sort(key=lambda x: -x[0])
    return scored[:k]
