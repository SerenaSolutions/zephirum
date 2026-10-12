#!/usr/bin/env python3
# ZYQL v1.0 PARSER — kernel ZEPHYRUM 1.12 — semântica 1/0/REFUSED
# Descendente recursivo puro, zero dependências. Nunca adivina: recusa.
import re

class Refused(Exception):
    def __init__(self, line, col, msg):
        super().__init__(f"L{line}:C{col} {msg}")
        self.line, self.col, self.msg = line, col, msg

SEC_RE = re.compile(r"^([A-Z][A-Z_]*):\s*(#.*)?$")
ENT_RE = re.compile(r"^([ \t]+)([a-z_][a-z0-9_]*):(.*)$")
BARE_RE = re.compile(r"^([ \t]+)([a-z_][a-z0-9_]*)\s*$")
NUM_RE = re.compile(r"^-?\d+(\.\d+)?$")
IDENT_RE = re.compile(r"^[a-z_][a-z0-9_]*$")
DIRAC_RE = re.compile(r"^([|<])([A-Za-z0-9_.]+)([|>])$")
ORDER = ["ASK", "CONTRACT", "MODEL", "BUDGET", "REQUIRE"]
REQUIRED = {"ASK", "CONTRACT", "MODEL"}

def _num(s, ln):
    s = s.strip()
    if not NUM_RE.match(s): raise Refused(ln, 1, f"número inválido: {s!r}")
    return float(s) if "." in s else int(s)

def _numlist(s, ln):
    parts = [p.strip() for p in s.split(",")]
    if parts and parts[-1] == "": raise Refused(ln, 1, "vírgula pendente")
    return [ _num(p, ln) for p in parts ]

def _atom_ok(side):
    side = side.strip()
    if not side or not re.match(r"^[A-Za-z0-9_.() ]+$", side):
        return False
    toks = [t.strip() for t in re.split(r"[+\-]", side) if t.strip()]
    return bool(toks) and all(NUM_RE.match(t) or IDENT_RE.match(t) for t in toks)

def _predicate(s, ln):
    for op in ("==", "!=", "<=", ">=", "<", ">"):
        if op in s:
            l, r = s.split(op, 1)
            if not _atom_ok(l) or not _atom_ok(r):
                raise Refused(ln, 1, f"átomo inválido no predicado: {s!r}")
            return {"lhs": l.strip(), "op": op, "rhs": r.strip()}
    raise Refused(ln, 1, "predicado sem comparador")

def _value(s, ln):
    s = s.strip()
    if NUM_RE.match(s): return _num(s, ln)
    if "," in s: return _numlist(s, ln)
    if s.startswith("|") or s.startswith("<"):
        d = DIRAC_RE.match(s)
        if not d or (s.startswith("|") and d.group(3) != ">") or \
           (s.startswith("<") and d.group(3) != "|"):
            raise Refused(ln, 1, f"literal Dirac malformado: {s!r}")
        return {"dirac": s}
    if IDENT_RE.match(s): return s
    raise Refused(ln, 1, f"valor ilegal: {s!r}")

def parse(text):
    """Retorna (1, AST, None) ou (0, None, motivo)."""
    try:
        return _parse(text)
    except Refused as e:
        return 0, None, str(e)

def _parse(text):
    lines = [ (i+1, l) for i, l in enumerate(text.splitlines()) ]
    lines = [ (n, l) for n, l in lines if l.strip() and not l.strip().startswith("#") ]
    if not lines: return 0, None, "programa vazio"
    ast, seen, last_idx = {}, set(), -1
    cur = None
    for ln, raw in lines:
        if SEC_RE.match(raw):
            name = raw.split(":")[0]
            if name not in ORDER:
                return 0, None, f"L{ln}: seção desconhecida {name!r}"
            idx = ORDER.index(name)
            if idx <= last_idx:
                return 0, None, f"L{ln}: seção {name} fora da ordem canônica"
            if name in seen:
                return 0, None, f"L{ln}: seção {name} duplicada"
            seen.add(name); last_idx = idx; cur = name; ast[name] = {}
            continue
        m = ENT_RE.match(raw)
        if m and cur:
            key, val = m.group(2), m.group(3)
            if key in ast[cur]:
                return 0, None, f"L{ln}: chave {key!r} duplicada em {cur}"
            if cur == "ASK":
                if key != "question":
                    return 0, None, f"L{ln}: ASK só aceita 'question'"
                ast[cur][key] = _predicate(val, ln)
            elif cur == "CONTRACT":
                ast[cur][key] = _num(val, ln)
            elif cur == "MODEL":
                if key == "type":
                    if "type" in ast[cur]:
                        return 0, None, f"L{ln}: 'type' duplicado"
                    if not IDENT_RE.match(val.strip()):
                        return 0, None, f"L{ln}: type inválido"
                ast[cur][key] = _value(val, ln)
            elif cur == "BUDGET":
                if not IDENT_RE.match(val.strip()):
                    return 0, None, f"L{ln}: valor de BUDGET inválido"
                ast[cur][key] = val.strip()
            else:
                return 0, None, f"L{ln}: entrada inesperada"
            continue
        m = BARE_RE.match(raw)
        if m and cur == "REQUIRE":
            ast[cur].setdefault("items", []).append(m.group(2))
            continue
        return 0, None, f"L{ln}:C1 sintaxe inválida"
    missing = REQUIRED - seen
    if missing:
        return 0, None, f"seções obrigatórias ausentes: {sorted(missing)}"
    if "type" not in ast.get("MODEL", {}):
        return 0, None, "MODEL sem 'type'"
    if "question" not in ast.get("ASK", {}):
        return 0, None, "ASK sem 'question'"
    return 1, ast, None

def canonical(ast):
    parts = []
    for s in ORDER:
        if s not in ast: continue
        parts.append(s + ":")
        for k, v in ast[s].items():
            if k == "items":
                for it in v: parts.append(f"    {it}")
            elif isinstance(v, dict) and "dirac" in v:
                parts.append(f"    {k}: {v['dirac']}")
            elif isinstance(v, dict) and "op" in v:
                parts.append(f"    {k}: {v['lhs']} {v['op']} {v['rhs']}")
            elif isinstance(v, list):
                parts.append(f"    {k}: " + ", ".join(str(x) for x in v))
            else:
                parts.append(f"    {k}: {v}")
    return "\n".join(parts) + "\n"

if __name__ == "__main__":
    import sys
    src = open(sys.argv[1]).read()
    ok, ast, err = parse(src)
    print("1 (OK)" if ok else f"REFUSED: {err}")
