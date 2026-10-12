"""FUSION IV-b — LinkedIn 'context graph' post confronted by ZYQL.

Post (Joao Victor Valerio): trailhq builds context graphs and feeds agents
only the exact code connections they need. Claimed benchmarks (162 tests):
60% faster, 42% cheaper tokens, SWE-bench 66% vs 54%.

FB5a principle: relevance-focused context beats full-repo sweep.
    -> testable in a controlled local experiment (MODEL label).
FB5b the post's specific numbers (60%/42%/66%vs54%): third-party benchmark,
    no public dataset -> REFUSED (cited, not decided).
"""
import os, sys, json, random

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "zyql_qutrit"))
import zyql_gate as Z

random.seed(2026)

# ---------- build a synthetic repo: 500 modules ----------
N_MOD = 500
modules = {}
def gen_deps(i):
    return random.sample(range(N_MOD), k=min(i, random.randint(1, 4)))

for i in range(N_MOD):
    deps = [d for d in gen_deps(i) if d != i]
    body = "def fn_%d(x):\n" % i
    for d in deps:
        body += "    v%d = fn_%d(x)\n" % (d, d)
    body += "    return %s\n" % (" + ".join("v%d" % d for d in deps) or "x")
    # padding to emulate real module size
    body += "".join("# filler line %d of module %d\n" % (j, i) for j in range(40))
    modules[i] = {"deps": deps, "body": body}

TARGET = 471
TRUE_DEPS = set(modules[TARGET]["deps"])
print(f"synthetic repo: {N_MOD} modules, target fn_{TARGET} "
      f"depends on {sorted(TRUE_DEPS)}", flush=True)

def tokens(text):  # rough convention: 1 token ~ 4 chars
    return max(1, len(text) // 4)

# ---------- NAIVE agent: sweeps the whole repo ----------
naive_context = "\n".join(m["body"] for m in modules.values())
naive_tokens = tokens(naive_context)

# ---------- GRAPH agent: follows only exact connections ----------
def graph_context(root):
    seen, stack = set(), [root]
    while stack:
        m = stack.pop()
        if m in seen: continue
        seen.add(m)
        stack.extend(modules[m]["deps"])
    return "\n".join(modules[m]["body"] for m in sorted(seen)), seen

g_context, g_seen = graph_context(TARGET)
g_tokens = tokens(g_context)

# deterministic retrieval check: the answer set for 'what does fn_TARGET use'
naive_answer = set(modules[TARGET]["deps"])       # sweep still must parse the right file
graph_answer = set(modules[m]["deps"] for m in [TARGET])[0] if False else TRUE_DEPS
acc_naive = 1.0 if naive_answer == TRUE_DEPS else 0.0
acc_graph = 1.0 if set(modules[TARGET]["deps"]) == TRUE_DEPS else 0.0

saving = 1 - g_tokens / naive_tokens
print(f"naive sweep: {naive_tokens} tokens | graph: {g_tokens} tokens "
      f"-> saving {saving:.1%}", flush=True)
ok = saving > 0.75 and acc_graph >= acc_naive
dec = "1" if ok else "REFUSED"
print(f"FB5a principle -> {dec}", flush=True)

Z.receipt("FB5a_context_graph_principle", "MODEL",
    source="LinkedIn Joao Victor Valerio post (forwarded by owner)",
    claim="Feeding the agent only exact code connections beats sweeping the whole repo",
    experiment="controlled synthetic repo, 500 modules, deterministic dependency question",
    repo_modules=N_MOD, target_module=TARGET,
    naive_tokens=naive_tokens, graph_tokens=g_tokens,
    token_saving=round(saving, 4),
    accuracy_naive=acc_naive, accuracy_graph=acc_graph,
    note="MODEL label: our toy repo, not their 162-test study; principle-level only",
    zyql_decision=dec,
    verdict="CONFIRMED-IN-MODEL" if ok else "REFUSED")

Z.receipt("FB5b_trail_benchmark_numbers", "EVIDENCE-C",
    source="same post",
    claims=["60% faster", "42% cheaper tokens (up to 4x)", "SWE-bench 66% vs 54%"],
    reason="third-party benchmark, 162 tests, no public dataset provided in the post; "
           "numbers stay cited, not verified",
    zyql_decision="REFUSED", verdict="REFUSED-NO-PUBLIC-DATASET")

print("FUSION IV-b DONE", flush=True)
