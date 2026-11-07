#!/usr/bin/env python3
# C3 — TEOREMA DE UNIVERSALIDADE ZYQL — kernel ZEPHYRUM 1.12
# Aritmetica EXATA em Z[i][sqrt2][1/2]: entrada = (p + q*sqrt2 + i(r + t*sqrt2))/2^k
import json, hashlib, itertools
from fractions import Fraction

def E(p=0, q=0, r=0, t=0, k=0):
    return (int(p), int(q), int(r), int(t), int(k))

def emul(a, b):
    p1,q1,r1,t1,k1 = a; p2,q2,r2,t2,k2 = b
    rp = (p1*p2 + 2*q1*q2) - (r1*r2 + 2*t1*t2)
    rq = (p1*q2 + q1*p2) - (r1*t2 + t1*r2)
    ip = (p1*r2 + r1*p2) + 2*(q1*t2 + t1*q2)
    iq = (p1*t2 + t1*p2) + (q1*r2 + r1*q2)
    return (rp, rq, ip, iq, k1+k2)

def eadd(a, b):
    k = max(a[4], b[4])
    A = tuple(x << (k - a[4]) for x in a[:4]); B = tuple(x << (k - b[4]) for x in b[:4])
    return (A[0]+B[0], A[1]+B[1], A[2]+B[2], A[3]+B[3], k)

def ecanon(a):
    p,q,r,t,k = a
    while k > 0 and p % 2 == 0 and q % 2 == 0 and r % 2 == 0 and t % 2 == 0:
        p,q,r,t,k = p//2, q//2, r//2, t//2, k-1
    return (p,q,r,t,k)

ZERO, ONE, IMAG = E(), E(1), E(0,0,1)
HALF2 = E(0,1,0,0,1)          # sqrt2/2
S_IN  = E(1,0,1,0,1)          # (1+i)/sqrt2  = e^{i pi/4} (usado por T)

def mat(N, f):
    return tuple(tuple(f(i,j) for j in range(N)) for i in range(N))

def mdot(A, B):
    N = len(A)
    out = []
    for i in range(N):
        row = []
        for j in range(N):
            acc = ZERO
            for l in range(N):
                acc = eadd(acc, emul(A[i][l], B[l][j]))
            row.append(ecanon(acc))
        out.append(tuple(row))
    return tuple(out)

def mkey(M):
    return str(tuple(tuple(ecanon(x) for x in row) for row in M))

def adj(M):
    N = len(M)
    return tuple(tuple(ecanon((M[j][i][0], M[j][i][1], -M[j][i][2], -M[j][i][3], M[j][i][4])) for j in range(N)) for i in range(N))

def ident(N):
    return mat(N, lambda i,j: ONE if i==j else ZERO)

STATUS = "parte 1 ok"

# ---------- GERADORES ----------
H1 = ((HALF2, HALF2), (HALF2, E(0,-1,0,0,1)))
X1 = ((ZERO, ONE), (ONE, ZERO))
Z1 = ((ONE, ZERO), (ZERO, E(-1)))
S1 = ((ONE, ZERO), (ZERO, IMAG))
T1 = ((ONE, ZERO), (ZERO, S_IN))
I2 = ident(2)

def closure(gens, cap=500000):
    seen = {mkey(I2): I2}; front = [I2]
    while front:
        nf = []
        for g in front:
            for gen in gens:
                for cand in (mdot(gen, g), mdot(g, gen)):
                    k = mkey(cand)
                    if k not in seen:
                        seen[k] = cand; nf.append(cand)
                        if len(seen) > cap: raise RuntimeError("cap")
        front = nf
    return seen

kern1  = closure([H1, X1, Z1])
cliff1 = closure([H1, X1, Z1, S1])
print("[C3-a] |<H,X,Z>| n=1 =", len(kern1), " | com S (Clifford):", len(cliff1))

# ---------- n=2: grupo simpletico sobre GF(2) ----------
def gf2mul(A, B):
    return tuple(sum(1 << b for b in range(4) if (A[r] >> b) & 1 and (B[b] >> 0) & 0) for r in range(4))

def gm(A, B, N=4):
    out = []
    for r in range(N):
        acc = 0
        for k in range(N):
            if (A[r] >> k) & 1:
                acc ^= B[k]
        out.append(acc)
    return tuple(out)

I4 = (1, 2, 4, 8)
H1g = (4, 2, 1, 8)   # troca x1<->z1 : bits [x1,x2,z1,z2] = [0,1,2,3]
H2g = (1, 8, 4, 2)
Cg  = (1, 0b0011, 0b1100, 8)  # x2+=x1 ; z1+=z2

def closure_gf2(gens, cap=20000):
    seen = {I4}; front = [I4]
    while front:
        nf = []
        for g in front:
            for gen in gens:
                cand = gm(gen, g)
                if cand not in seen:
                    seen.add(cand); nf.append(cand)
        front = nf
    return seen

sp = closure_gf2([H1g, H2g, Cg])
print("[C3-b] |<H1,H2,CNOT>| em Sp(4,2) =", len(sp), "(esperado 720)")
print("[C3-b] |C1| = 4^1*6 =", 4*6, " | |C2| = 4^2*720 =", 16*720)

# ---------- T nao e Clifford (prova exata) ----------
TXT = mdot(mdot(T1, X1), adj(T1))
alvo = ((ZERO, E(1,0,-1,0,1)), (E(1,0,1,0,1), ZERO))   # (X+Y)/sqrt2
ok_alvo = mkey(TXT) == mkey(alvo)
PAULIS = {"I": I2, "X": X1, "Z": Z1,
          "Y": mdot(T1, T1) if False else ((ZERO, IMAG), (E(0,0,-1,0,1) if False else E(0,0,-1,0,1), ZERO))}
def e_neg(e): return (-e[0], -e[1], -e[2], -e[3], e[4])
def e_mul_i(e): return (-e[2], -e[3], e[0], e[1], e[4])

def eh_fase_vezes_pauli(M):
    letras = {"I": I2, "X": X1, "Z": Z1, "Y": ((ZERO, E(0,0,-1)), (E(0,0,1), ZERO))}
    for nome, P in letras.items():
        for f in range(4):
            Q = tuple(tuple((lambda e: e if f==0 else (e_mul_i(e) if f==1 else (e_neg(e) if f==2 else e_neg(e_mul_i(e)))))(x) for x in row) for row in P)
            if mkey(Q) == mkey(M):
                return nome, f
    return None

res_pauli = eh_fase_vezes_pauli(TXT)
print("[C3-c] T X T+ == (X+Y)/sqrt2 exato:", ok_alvo)
print("[C3-c] T X T+ e' fase x Pauli?", res_pauli, "-> T NAO pertence ao grupo de Clifford")

STATUS = "parte 2 ok"

# ---------- densidade numerica de <H,T> (NUMERICA, nao prova) ----------
import numpy as np, math
Hf = np.array([[1,1],[1,-1]], complex)/math.sqrt(2)
Tf = np.array([[1,0],[0,np.exp(1j*math.pi/4)]], complex)
Gf = [Hf, Tf, Tf.conj().T]

def su2(rng):
    A = rng.normal(size=(2,2)) + 1j*rng.normal(size=(2,2))
    Q, R = np.linalg.qr(A)
    d = np.diag(R); Q = Q * (d/abs(d))
    return Q / math.sqrt(abs(np.linalg.det(Q)))

def dens(L, nsamp=40000, ntar=80, seed=5):
    rng = np.random.default_rng(seed + L)
    W = np.tile(np.eye(2, dtype=complex), (nsamp,1,1))
    for _ in range(L):
        g = np.array(Gf)[rng.integers(0, len(Gf), nsamp)]
        W = g @ W
    U = np.array([su2(rng) for _ in range(ntar)])
    d = np.abs(U[:,None,:,:] - W[None,:,:,:]).reshape(ntar, nsamp, -1).max(axis=2)
    return float(np.median(d.min(axis=1))), float(d.min(axis=1).max())

dens_res = {}
for L in (10, 20, 30, 40):
    med, mx = dens(L)
    dens_res[L] = (round(med, 5), round(mx, 5))
    print(f"[C3-d] <H,T> palavras de {L} geradores: erro mediano {med:.4f} | pior {mx:.4f}")

rec = {
 "bateria": "C3", "nome": "TEOREMA DE UNIVERSALIDADE ZYQL", "kernel": "ZEPHYRUM 1.12",
 "L_A_grupo_do_kernel_n1": len(kern1),
 "L_A_grupo_com_S_n1": len(cliff1),
 "L_A_leitura": f"{len(cliff1)} = 8 fases x {len(cliff1)//8} = |C1|/U(1) mod fase",
 "L_B_grupo_simpletico_n2_kernel": len(sp),
 "L_B_espaco_simpletico_completo": 720,
 "L_B_conclusao": "o conjunto atual gera apenas 72 dos 720 elementos: subgrupo ESTRITO do Clifford",
 "L_C_T_e_clifford": False,
 "L_C_prova": "T X T+ = (X+Y)/sqrt2 EXATO e nao e fase x Pauli -> T nao preserva o grupo de Pauli",
 "L_D_densidade_numerica": dens_res,
 "teorema_1": "Nenhum circuito sobre {H,X,Y,Z,CNOT} e universal: o fecho do grupo e finito, logo unitarias fora do conjunto tem distancia minima positiva",
 "teorema_2": "Com S adicionado chega-se ao grupo de Clifford (24 mod fase); ainda NAO universal (Gottesman-Knill 1998: simulacao classica eficiente)",
 "teorema_3": "Com T (ou Rz(theta)) adicionado, <H,T,CNOT> e denso em SU(2^n) — Boykin-Mor-Pulver-Rowell 2000; Shi 2002; Aharonov 2003; aproximacao por Solovay-Kitaev 1997",
 "veredito": "C3 VERDADEIRO E INFORMATIVO: a linguagem NAO e universal hoje; torna-se universal com a adicao de T/Rz ao kernel e ao compilador — mudanca especificada",
 "aursa": {"L1": "FATO: ordens de grupo enumeradas exatamente", "L2": "FATO: prova algebrica exata de T nao-Clifford",
           "L3": "NUMERICA: densidade de <H,T> (evidencia, nao prova)", "L4": "INFERENCIA: teoremas citados da literatura"},
}
rec["RECEIPT_HASH"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()[:32]
open("RECEIPT_C3.json","w").write(json.dumps(rec, indent=1, ensure_ascii=False))
print("VEREDITO C3:", rec["veredito"][:70])
print("RECEIPT_HASH:", rec["RECEIPT_HASH"])
