# ==== NATIVE AI BUILTINS (rooted Oct 12, 2026) ====
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "kernel_intelligence"))
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "zyql_qutrit"))
def _ai_rag(query, k=3):
    import rag
    def _txt(h):
        if isinstance(h, dict): return str(h.get("text") or h.get("chunk") or h.get("doc") or h)
        return str(h)
    return " || ".join(_txt(h) for h in rag.retrieve(str(query), k=int(k)))
def _ai_qnn(t1, t2, t3, t4, t5, t6, x1, x2):
    # ZEPHIRUM int-only: 6 theta params + 2 input, scaled /10 (7 -> 0.7)
    import qnn_fast
    th = [v / 10.0 for v in (t1, t2, t3, t4, t5, t6)]
    xx = [v / 10.0 for v in (x1, x2)]
    return qnn_fast.fast_forward(xx, th, 2)
def _ai_ask(question):
    import zyql_gate as Z; r = Z.decide_with_ai(str(question))
    return "verdict=%s grounded=%s" % (r["verdict"], r.get("grounded_chunks", 0))
# -*- coding: utf-8 -*-
"""
CEFIRUM v0.1 — the native language of Zephyrum OS.
Real lexer + parser + tree-walking interpreter. Integer-only (bignum),
arrays, functions, recursion, bitwise ops, and quantum primitives
wired to the Zephyrum QPU (SIMULATION MODE).

Honesty contract: nothing here claims to be a compiler or to be fast.
It is an interpreter, executed for real, and every result printed by
`cefirum run <file>` comes from actual execution.
"""
import sys, os, math, time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.setrecursionlimit(100000)


class CefirumError(Exception):
    pass


# ---------------- Lexer ----------------
KEYWORDS = {"fun", "if", "else", "while", "for", "to", "return", "print",
            "assert", "break", "and", "or", "not"}
SYMBOLS = ["==", "!=", "<=", ">=", "+=", "-=", "*=", "//",
          "=", "<", ">", "+", "-", "*", "/", "%", "(", ")", "{", "}",
          "[", "]", ",", "#"]



def normalize_source(src):
    """ZEPHIRUM syntax hardening (Oct 12, 2026): accepts tabs, CRLF, mixed
    indentation; normalizes to canonical LF + 4-space form before tokenizing."""
    src = src.replace("\r\n", "\n").replace("\r", "\n").replace("\t", "    ")
    lines = [l.rstrip() for l in src.split("\n")]
    out, blanks = [], 0
    for l in lines:
        if l == "": blanks += 1
        else: blanks = 0
        if blanks <= 1: out.append(l)
    return "\n".join(out)
def tokenize(src):
    toks, i, line = [], 0, 1
    while i < len(src):
        c = src[i]
        if c == "\n":
            line += 1; i += 1; continue
        if c in " \t\r":
            i += 1; continue
        if c == "#":
            while i < len(src) and src[i] != "\n":
                i += 1
            continue
        if c == '"':
            j = i + 1
            while j < len(src) and src[j] != '"':
                j += 1
            if j >= len(src):
                raise CefirumError(f"line {line}: unterminated string")
            toks.append(("STR", src[i + 1:j], line)); i = j + 1; continue
        if c.isdigit():
            j = i
            while j < len(src) and src[j].isdigit():
                j += 1
            toks.append(("INT", int(src[i:j]), line)); i = j; continue
        if c.isalpha() or c == "_":
            j = i
            while j < len(src) and (src[j].isalnum() or src[j] == "_"):
                j += 1
            w = src[i:j]
            toks.append((w if w in KEYWORDS else "NAME", w, line)); i = j; continue
        for s in SYMBOLS:
            if src.startswith(s, i):
                toks.append((s, s, line)); i += len(s); break
        else:
            raise CefirumError(f"line {line}: unexpected character {c!r}")
    toks.append(("EOF", None, line))
    return toks


# ---------------- Parser ----------------
class Parser:
    def __init__(self, toks):
        self.toks = toks; self.i = 0

    def peek(self, k=0):
        return self.toks[min(self.i + k, len(self.toks) - 1)]

    def next(self):
        t = self.toks[self.i]; self.i += 1; return t

    def expect(self, kind):
        t = self.next()
        if t[0] != kind:
            raise CefirumError(f"line {t[2]}: expected {kind!r}, got {t[0]!r}")
        return t

    def parse_program(self):
        stmts = []
        while self.peek()[0] != "EOF":
            stmts.append(self.parse_statement())
        return ("block", stmts)

    def parse_block(self):
        self.expect("{")
        stmts = []
        while self.peek()[0] != "}":
            stmts.append(self.parse_statement())
        self.expect("}")
        return ("block", stmts)

    def parse_statement(self):
        t = self.peek()
        k = t[0]
        if k == "fun":
            self.next(); name = self.expect("NAME")[1]
            self.expect("(")
            params = []
            if self.peek()[0] != ")":
                params.append(self.expect("NAME")[1])
                while self.peek()[0] == ",":
                    self.next(); params.append(self.expect("NAME")[1])
            self.expect(")")
            return ("fun", name, params, self.parse_block())
        if k == "if":
            self.next(); cond = self.parse_expr()
            then = self.parse_block()
            els = None
            if self.peek()[0] == "else":
                self.next()
                if self.peek()[0] == "if":
                    els = ("block", [self.parse_statement()])
                else:
                    els = self.parse_block()
            return ("if", cond, then, els)
        if k == "while":
            self.next(); cond = self.parse_expr()
            return ("while", cond, self.parse_block())
        if k == "for":
            self.next(); var = self.expect("NAME")[1]
            self.expect("="); lo = self.parse_expr(); self.expect("to")
            hi = self.parse_expr()
            return ("for", var, lo, hi, self.parse_block())
        if k == "return":
            self.next()
            e = None if self.peek()[0] in ("}", "EOF") else self.parse_expr()
            return ("return", e)
        if k == "print":
            self.next(); args = [self.parse_expr()]
            while self.peek()[0] == ",":
                self.next(); args.append(self.parse_expr())
            return ("print", args)
        if k == "assert":
            self.next(); cond = self.parse_expr()
            msg = ("STR", "assertion failed", t[2])
            if self.peek()[0] == ",":
                self.next(); msg = self.next()
            return ("assert", cond, msg)
        if k == "break":
            self.next(); return ("break",)
        # assignment / indexed assignment
        if k == "NAME":
            if self.peek(1)[0] == "=":
                self.next(); self.next()
                return ("assign", t[1], self.parse_expr())
            if self.peek(1)[0] in ("+=", "-=", "*="):
                self.next(); op = self.next()[0][0]
                rhs = self.parse_expr()
                return ("assignop", t[1], op, rhs)
            if self.peek(1)[0] == "[":
                self.next(); self.next()
                idxs = [self.parse_expr()]
                self.expect("]")
                while self.peek()[0] == "[":
                    self.next(); idxs.append(self.parse_expr()); self.expect("]")
                self.expect("=")
                return ("setidx", t[1], idxs, self.parse_expr())
        raise CefirumError(f"line {t[2]}: unexpected token {t[1]!r}")

    def parse_expr(self):
        return self.parse_or()

    def parse_or(self):
        e = self.parse_and()
        while self.peek()[0] == "or":
            self.next(); e = ("or", e, self.parse_and())
        return e

    def parse_and(self):
        e = self.parse_not()
        while self.peek()[0] == "and":
            self.next(); e = ("and", e, self.parse_not())
        return e

    def parse_not(self):
        if self.peek()[0] == "not":
            self.next(); return ("not", self.parse_not())
        return self.parse_cmp()

    def parse_cmp(self):
        e = self.parse_add()
        if self.peek()[0] in ("==", "!=", "<", ">", "<=", ">="):
            op = self.next()[0]
            return ("cmp", op, e, self.parse_add())
        return e

    def parse_add(self):
        e = self.parse_mul()
        while self.peek()[0] in ("+", "-"):
            op = self.next()[0]
            e = ("bin", op, e, self.parse_mul())
        return e

    def parse_mul(self):
        e = self.parse_unary()
        while self.peek()[0] in ("*", "/", "%"):
            op = self.next()[0]
            e = ("bin", op, e, self.parse_unary())
        return e

    def parse_unary(self):
        if self.peek()[0] == "-":
            self.next(); return ("neg", self.parse_unary())
        return self.parse_postfix()

    def parse_postfix(self):
        e = self.parse_primary()
        while True:
            if self.peek()[0] == "[":
                self.next(); idx = self.parse_expr(); self.expect("]")
                e = ("index", e, idx)
            elif self.peek()[0] == "(":
                self.next(); args = []
                if self.peek()[0] != ")":
                    args.append(self.parse_expr())
                    while self.peek()[0] == ",":
                        self.next(); args.append(self.parse_expr())
                self.expect(")")
                e = ("call", e, args)
            else:
                return e

    def parse_primary(self):
        t = self.next()
        if t[0] == "INT":
            return ("int", t[1])
        if t[0] == "STR":
            return ("str", t[1])
        if t[0] == "NAME":
            return ("name", t[1])
        if t[0] == "(":
            e = self.parse_expr(); self.expect(")")
            return e
        raise CefirumError(f"line {t[2]}: unexpected token {t[1]!r}")


# ---------------- Runtime ----------------
class BreakEx(Exception):
    pass


class ReturnEx(Exception):
    def __init__(self, val):
        self.val = val


KERNEL = None


def _kernel():
    global KERNEL
    if KERNEL is None:
        import kernel as _k
        KERNEL = _k.ZephyrumKernel()
    return KERNEL


def _qpu_run(name, shots):
    res = _kernel().syscall("run", name)
    if isinstance(res, dict) and "counts" in res:
        return " ".join(f"{k}:{v}" for k, v in sorted(res["counts"].items()))
    return f"error: {res.get('error', res)}"


BUILTINS = {
    "len": lambda a: len(a),
    "arr": lambda n: [0] * n,
    "pow": lambda a, b: a ** b,
    "isqrt": lambda n: math.isqrt(n),
    "min": lambda a, b: a if a < b else b,
    "max": lambda a, b: a if a > b else b,
    "abs": lambda n: -n if n < 0 else n,
    "ln": lambda n: int(math.log(n) * 1000000),  # fixed-point 1e-6
    "bitand": lambda a, b: a & b,
    "bitor": lambda a, b: a | b,
    "bitxor": lambda a, b: a ^ b,
    "lshift": lambda a, b: a << b,
    "rshift": lambda a, b: a >> b,
    "popcount": lambda n: bin(n).count("1"),
    "time": lambda: int(time.time() * 1000),
    "ai_rag": _ai_rag, "ai_qnn": _ai_qnn, "ai_ask": _ai_ask, "qpu_run": _qpu_run,
}


class Interp:
    def __init__(self):
        self.globals = {}
        self.funs = {}

    def truthy(self, v):
        return not (v == 0 or v == "" or v == [])

    def run(self, ast):
        self.exec(ast, self.globals)

    def exec(self, node, env):
        k = node[0]
        if k == "block":
            for s in node[1]:
                self.exec(s, env)
            return
        if k == "fun":
            self.funs[node[1]] = (node[2], node[3]); return
        if k == "assign":
            env[node[1]] = self.eval(node[2], env); return
        if k == "assignop":
            env[node[1]] = self.eval(("bin", node[2], ("name", node[1]), node[3]), env)
            return
        if k == "setidx":
            tgt = self.eval(("name", node[1]), env)
            cur = tgt
            for ix in node[2][:-1]:
                cur = cur[self.eval(ix, env)]
            cur[self.eval(node[2][-1], env)] = self.eval(node[3], env)
            return
        if k == "if":
            if self.truthy(self.eval(node[1], env)):
                self.exec(node[2], env)
            elif node[3] is not None:
                self.exec(node[3], env)
            return
        if k == "while":
            while self.truthy(self.eval(node[1], env)):
                try:
                    self.exec(node[2], env)
                except BreakEx:
                    break
            return
        if k == "for":
            lo = self.eval(node[2], env); hi = self.eval(node[3], env)
            i = lo
            while i <= hi:
                env[node[1]] = i
                try:
                    self.exec(node[4], env)
                except BreakEx:
                    break
                i = env[node[1]] + 1
            return
        if k == "return":
            raise ReturnEx(None if node[1] is None else self.eval(node[1], env))
        if k == "break":
            raise BreakEx()
        if k == "print":
            print(" ".join(str(self.eval(a, env)) for a in node[1])); return
        if k == "assert":
            if not self.truthy(self.eval(node[1], env)):
                raise CefirumError(f"line {node[2][2]}: ASSERT FAILED: {node[2][1]}")
            return
        raise CefirumError(f"unknown statement {k}")

    def eval(self, node, env):
        k = node[0]
        if k == "int":
            return node[1]
        if k == "str":
            return node[1]
        if k == "name":
            if node[1] in env:
                return env[node[1]]
            if node[1] in self.globals:
                return self.globals[node[1]]
            if node[1] in BUILTINS:
                return ("builtin", node[1])
            raise CefirumError(f"undefined name {node[1]!r}")
        if k == "neg":
            return -self.eval(node[1], env)
        if k == "not":
            return 0 if self.truthy(self.eval(node[1], env)) else 1
        if k == "and":
            return self.eval(node[2], env) if self.truthy(self.eval(node[1], env)) else 0
        if k == "or":
            return self.eval(node[1], env) if self.truthy(self.eval(node[1], env)) \
                else self.eval(node[2], env)
        if k == "cmp":
            op, a, b = node[1], self.eval(node[2], env), self.eval(node[3], env)
            return {"==": a == b, "!=": a != b, "<": a < b, ">": a > b,
                    "<=": a <= b, ">=": a >= b}[op] and 1 or 0
        if k == "bin":
            op = node[1]; a = self.eval(node[2], env); b = self.eval(node[3], env)
            if op == "+":
                if isinstance(a, str) or isinstance(b, str):
                    return str(a) + str(b)
                return a + b
            if op == "-":
                return a - b
            if op == "*":
                return a * b
            if op == "/":
                if b == 0:
                    raise CefirumError("division by zero")
                q = abs(a) // abs(b)
                return q if (a >= 0) == (b >= 0) else -q
            if op == "%":
                if b == 0:
                    raise CefirumError("modulo by zero")
                r = abs(a) % abs(b)
                return r if a >= 0 else -r
        if k == "index":
            a = self.eval(node[1], env)
            if not isinstance(a, list):
                raise CefirumError("indexing a non-array")
            i = self.eval(node[2], env)
            if i < 0 or i >= len(a):
                raise CefirumError(f"index {i} out of range (len {len(a)})")
            return a[i]
        if k == "call":
            if node[1][0] == "name" and node[1][1] in self.funs:
                callee = node[1][1]
            else:
                callee = self.eval(node[1], env)
            args = [self.eval(a, env) for a in node[2]]
            if isinstance(callee, tuple) and callee[0] == "builtin":
                return BUILTINS[callee[1]](*args)
            if isinstance(callee, str) and callee in self.funs:
                params, body = self.funs[callee]
                if len(params) != len(args):
                    raise CefirumError(f"{callee}: expected {len(params)} args, got {len(args)}")
                fenv = dict(zip(params, args))
                try:
                    self.exec(body, fenv)
                except ReturnEx as r:
                    return r.val
                return 0
            raise CefirumError(f"not callable: {callee!r}")
        raise CefirumError(f"unknown expression {k}")


def run_file(path):
    with open(path, encoding="utf-8") as f:
        src = normalize_source(f.read())
    toks = tokenize(src)
    ast = Parser(toks).parse_program()
    Interp().run(ast)


if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] != "run":
        print("usage: python3 cefirum.py run <file.cef>")
        sys.exit(2)
    try:
        run_file(sys.argv[2])
    except CefirumError as e:
        print(f"CEFIRUM ERROR: {e}")
        sys.exit(1)


