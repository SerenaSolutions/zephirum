#!/usr/bin/env python3
# BATERIA 46 — DECODER DE IA AUDITADO PELA REGUA EXATA — kernel ZEPHYRUM 1.12
# Codigo de superficie d=3 (bateria 43) + decoder neural (numpy, Adam) + avaliacao EXAUSTIVA
import numpy as np, json, hashlib
popc = lambda x: bin(x).count("1")


def basis(rows):
    b = []
    for r in rows:
        for x in b:
            r = min(r, r ^ x)
        if r:
            b.append(r)
    return b


def rank(rows): return len(basis(rows))


def inspan(v, b):
    for x in b:
        v = min(v, v ^ x)
    return v == 0


def build(d, io, et, sl, sr, st, sb):
    L, R, T, B = et
    f = []
    for i in range(d - 1):
        for j in range(d - 1):
            m = (1 << (i*d+j)) | (1 << ((i+1)*d+j)) | (1 << (i*d+j+1)) | (1 << ((i+1)*d+j+1))
            f.append((m, 'X' if ((i + j) & 1) == io else 'Z'))
    def edge(i, j, t):
        m = k = 0
        for (x, y) in [(i, j), (i+1, j), (i, j+1), (i+1, j+1)]:
            if 0 <= x < d and 0 <= y < d:
                m |= 1 << (x*d+y)
                k += 1
        return (m, t) if k >= 2 else None
    for j in range(d - 1):
        if j % 2 == sl:
            e = edge(-1, j, L)
            if e: f.append(e)
        if j % 2 == sr:
            e = edge(d-1, j, R)
            if e: f.append(e)
        if j % 2 == st:
            e = edge(j, -1, T)
            if e: f.append(e)
        if j % 2 == sb:
            e = edge(j, d-1, B)
            if e: f.append(e)
    return [m for m, t in f if t == 'X'], [m for m, t in f if t == 'Z']


def minw(n, Hchk, Hspan):
    b = basis(Hspan)
    for w in range(1, n + 1):
        for v in range(1, 1 << n):
            if popc(v) != w:
                continue
            if any(popc(h & v) & 1 for h in Hchk):
                continue
            if not inspan(v, b):
                return w
    return None


def find_code(d):
    n = d * d
    for io in (True, False):
        for L in 'XZ':
            for R in 'XZ':
                for T in 'XZ':
                    for B in 'XZ':
                        for sl in (0, 1):
                            for sr in (0, 1):
                                for st in (0, 1):
                                    for sb in (0, 1):
                                        HX, HZ = build(d, io, (L, R, T, B), sl, sr, st, sb)
                                        if len(HX) + len(HZ) != n - 1:
                                            continue
                                        if rank(HX) != len(HX) or rank(HZ) != len(HZ):
                                            continue
                                        if any(popc(a & b) & 1 for a in HX for b in HZ):
                                            continue
                                        cx = cz = 0
                                        for h in HX: cx |= h
                                        for h in HZ: cz |= h
                                        if cx != (1 << n) - 1 or cz != (1 << n) - 1:
                                            continue
                                        if minw(n, HZ, HX) != d or minw(n, HX, HZ) != d:
                                            continue
                                        return HX, HZ
    raise SystemExit("sem construcao")


d = 3
n = d * d
HX, HZ = find_code(d)
bX, bZ = basis(HX), basis(HZ)
print(f"[L0] codigo d={d}: {len(HX)} X-stabs + {len(HZ)} Z-stabs, k=1, distancia {d} exata")


def synd(val, stabs):
    s = 0
    for i, h in enumerate(stabs):
        s |= (popc(h & val) & 1) << i
    return s


# ---- L1: decodificador EXATO (lider de peso minimo) ----
leaderX = {i: (99, 0) for i in range(16)}
leaderZ = {i: (99, 0) for i in range(16)}
for val in range(1 << n):
    sx, sz, w = synd(val, HZ), synd(val, HX), popc(val)
    if w < leaderX[sx][0]: leaderX[sx] = (w, val)
    if w < leaderZ[sz][0]: leaderZ[sz] = (w, val)
print("[L1] tabela de lideres exata (16 sindromes) construida")


# ---- treino neural com Adam de verdade ----
def fit(X, Y, epochs=8000, lr0=0.01, hid=64, seed=7):
    r = np.random.default_rng(seed)
    P = [r.normal(0, .5, (X.shape[1], hid)).astype(np.float32), np.zeros(hid, np.float32),
         r.normal(0, .5, (hid, hid)).astype(np.float32), np.zeros(hid, np.float32),
         r.normal(0, .5, (hid, Y.shape[1])).astype(np.float32), np.zeros(Y.shape[1], np.float32)]
    M = [np.zeros_like(p) for p in P]
    V = [np.zeros_like(p) for p in P]
    t = 0
    lr = lr0
    for ep in range(epochs):
        h1 = np.tanh(X @ P[0] + P[1])
        h2 = np.tanh(h1 @ P[2] + P[3])
        out = 1/(1+np.exp(-(h2 @ P[4] + P[5])))
        g = (out - Y) / len(X)
        gW3 = h2.T @ g
        gb3 = g.sum(0)
        g2 = (g @ P[4].T) * (1 - h2**2)
        gW2 = h1.T @ g2
        gb2 = g2.sum(0)
        g1 = (g2 @ P[2].T) * (1 - h1**2)
        gW1 = X.T @ g1
        gb1 = g1.sum(0)
        t += 1
        for i, gr in enumerate([gW1, gb1, gW2, gb2, gW3, gb3]):
            M[i] = .9*M[i] + .1*gr
            V[i] = .999*V[i] + .001*gr*gr
            P[i] -= lr*(M[i]/(1-.9**t))/(np.sqrt(V[i]/(1-.999**t)) + 1e-8)
        if ep % 3000 == 2999:
            lr *= .5
    h1 = np.tanh(X @ P[0] + P[1])
    h2 = np.tanh(h1 @ P[2] + P[3])
    out = 1/(1+np.exp(-(h2 @ P[4] + P[5])))
    loss = -np.mean(Y*np.log(np.clip(out, 1e-9, 1)) + (1-Y)*np.log(np.clip(1-out, 1e-9, 1)))
    mism = int(((out > .5).astype(int) != Y).sum())
    return P, float(loss), mism


def decide(P, sbit):
    x = np.zeros((1, X_dim), np.float32)
    for b in range(X_dim):
        x[0, b] = (sbit >> b) & 1
    h1 = np.tanh(x @ P[0] + P[1])
    h2 = np.tanh(h1 @ P[2] + P[3])
    out = (1/(1+np.exp(-(h2 @ P[4] + P[5]))))[0] > .5
    v = 0
    for q in range(n):
        if out[q]:
            v |= 1 << q
    return v


def bitvec(s, width=4):
    return [(s >> b) & 1 for b in range(width)]


X_dim = 4

# ---- L2: V2 = aprendizado supervisionado padrao (rotulos = erro verdadeiro) ----
rng = np.random.default_rng(1701)
M_SAMPLES = 30000
Xs = np.zeros((M_SAMPLES, 4), np.float32)
Xs2 = np.zeros((M_SAMPLES, 4), np.float32)
Ys = np.zeros((M_SAMPLES, n), np.float32)
for k in range(M_SAMPLES):
    v = 0
    for q in range(n):
        if rng.random() < 2 * 0.01 / 3:
            v |= 1 << q
    Xs[k] = bitvec(synd(v, HZ))      # lado X: sindrome via Z-stabs
    Xs2[k] = bitvec(synd(v, HX))     # lado Z: sindrome via X-stabs
    for q in range(n):
        Ys[k, q] = (v >> q) & 1
P2, loss2, mism2 = fit(Xs, Ys, epochs=8000)
P2b, loss2b, mism2b = fit(Xs2, Ys, epochs=8000, seed=11)
print(f"[L2] V2 supervisionado: loss {loss2:.4f}/{loss2b:.4f}, divergencias {mism2}/{mism2b}")
mlX = {s: decide(P2, s) for s in range(16)}
mlZ = {s: decide(P2b, s) for s in range(16)}

# ---- V3: imitacao do lider exato (16 rotulos, o teto alcancavel) ----
Xi = np.zeros((16, 4), np.float32)
YiX = np.zeros((16, n), np.float32)
YiZ = np.zeros((16, n), np.float32)
for s in range(16):
    Xi[s] = bitvec(s)
    vx, vz = leaderX[s][1], leaderZ[s][1]
    for q in range(n):
        YiX[s, q] = (vx >> q) & 1
        YiZ[s, q] = (vz >> q) & 1
P3X, loss3x, mism3x = fit(Xi, YiX, epochs=20000, lr0=0.01, seed=3)
P3Z, loss3z, mism3z = fit(Xi, YiZ, epochs=20000, lr0=0.01, seed=5)
print(f"[V3] imitacao: divergencias X={mism3x}/144 Z={mism3z}/144")
mlXiX = {s: decide(P3X, s) for s in range(16)}
mlXiZ = {s: decide(P3Z, s) for s in range(16)}


# ---- L3: avaliacao EXAUSTIVA (262144 padroes) para os tres decoders ----
def evaluate(decX, decZ):
    c = {}
    for pat in range(4 ** n):
        ex = ez = 0
        p_ = pat
        for q in range(n):
            k = p_ & 3
            p_ >>= 2
            if k in (1, 3): ex |= 1 << q
            if k in (2, 3): ez |= 1 << q
        w = popc(ex | ez)
        rx = ex ^ decX[synd(ex, HZ)]
        rz = ez ^ decZ[synd(ez, HX)]
        if not (inspan(rx, bX) and inspan(rz, bZ)):
            c[w] = c.get(w, 0) + 1
    return c


cE = evaluate({s: leaderX[s][1] for s in range(16)}, {s: leaderZ[s][1] for s in range(16)})
cM = evaluate(mlX, mlZ)
cI = evaluate(mlXiX, mlXiZ)
print("[L3] avaliacao exaustiva concluida para exato, V2 e V3")


def PL(counts, p):
    return sum(c * ((1 - p) ** (n - w)) * ((p / 3) ** w) for w, c in counts.items())


def pthr(counts):
    lo, hi = 1e-7, 1.0
    for _ in range(90):
        mid = (lo + hi) / 2
        if PL(counts, mid) >= mid:
            hi = mid
        else:
            lo = mid
    return lo


base = PL(cE, .01)
res = {
    "bateria": 46,
    "nome": "DECODER DE IA AUDITADO PELA REGUA EXATA",
    "kernel": "ZEPHYRUM 1.12",
    "codigo": f"d={d}, n={n}, k=1, distancia {d} exata",
    "P_L_exato_p0.01": round(base, 8),
    "P_L_V2_supervisionado_p0.01": round(PL(cM, .01), 8),
    "razao_V2_sobre_exato": round(PL(cM, .01) / base, 3),
    "P_L_V3_imitacao_p0.01": round(PL(cI, .01), 8),
    "razao_V3_sobre_exato": round(PL(cI, .01) / base, 3),
    "V3_bits_divergentes_X": mism3x, "V3_bits_divergentes_Z": mism3z,
    "pseudo_limiar_exato": round(pthr(cE), 5),
    "pseudo_limiar_V2": round(pthr(cM), 5),
    "pseudo_limiar_V3": round(pthr(cI), 5),
    "falhas_por_peso_exato": dict(sorted(cE.items())),
    "falhas_por_peso_V2": dict(sorted(cM.items())),
    "falhas_por_peso_V3": dict(sorted(cI.items())),
    "padroes_avaliados": 4 ** n,
    "aursa": {
        "L0": "FATO: codigo construido e verificado (postos, comutacao, cobertura, distancia)",
        "L1": "FATO: lider de coset exato por enumeracao — OTIMO por construcao sob ruido iid",
        "L2": "EXPERIMENTAL: rede neural supervisionada padrao, nao certificavel por instancia",
        "V3": "EXPERIMENTAL: rede neural treinada com rotulos exatos (teto alcancavel)",
        "L3": "FATO: avaliacao exaustiva dos 262144 padroes"
    },
    "teoria": "o lider de coset minimiza a probabilidade de erro logico sob ruido iid; nenhum decoder pode supera-lo neste criterio. O valor de um decoder neural e VELOCIDADE em codigos grandes, nunca precisao acima do otimo",
    "rotulo": "o neural NAO e certificado; medido exatamente contra o otimo"
}
res["RECEIPT_HASH"] = hashlib.sha256(json.dumps(res, sort_keys=True).encode()).hexdigest()[:32]
open("sephirum/prototype/ml_decoder/RECEIPT_46.json", "w").write(json.dumps(res, indent=1, ensure_ascii=False))
print(json.dumps(res, indent=1, ensure_ascii=False))
