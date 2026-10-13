# QLAB-002 C6 — VERIFY: recomputação independente + tripartição + critérios A4-A6
import json, math, os
import numpy as np
F=os.path.dirname(os.path.abspath(__file__))
def J(p): return os.path.join(F,p)
ci=json.load(open(J("circuitos_002c6.json"))); hw=json.load(open(J("hw_002c6.json"))); refs=json.load(open(J("refs_002c6.json")))
idx={}
for i,c in enumerate(ci["circuitos"]): idx[(round(c["theta"],6),c["base"])]=i
def bit(key,q): return int(key.replace(" ","")[3-q])
def exp_from_counts(counts,pl):
    N=sum(counts.values()); s=0.0
    for k,v in counts.items():
        e=1.0
        for q in pl: e*= (1-2*bit(k,q)) if pl[q]!="I" else 1.0
        s+=v*e
    return s/N
def sigma_from_counts(counts,pl):
    N=sum(counts.values()); vals=[]
    for k,v in counts.items():
        e=1.0
        for q in pl: e*= (1-2*bit(k,q)) if pl[q]!="I" else 1.0
        vals += [e]*v
    return math.sqrt(max(0.0,(1.0-(sum(vals)/N)**2)/N))
# A6: DUAS implementações independentes (regra de produto vs soma por shot)
def exp_v2(counts,pl):
    N=sum(counts.values()); acc=0.0
    for k,v in counts.items():
        p=1
        for q,ch in sorted(pl.items()):
            b=1 if k.replace(" ","")[3-q]=="1" else 0
            p*= (1-2*b)
        acc += v*p
    return acc/N
def energy(theta,which):
    th=round(theta,6); E=0.0; details=[]
    for tc in ci["termos"]:
        c=tc["c"]; pl={int(k):v for k,v in tc["pl"].items()}
        base = "".join(pl.get(q,"I") for q in range(4))
        base = "Z" if set(pl.values())<= {"Z"} else base
        cts = hw["counts"][idx[(th,base)]] if which=="hw" else refs[f"{th}|{base}"][which] if isinstance(which,int) else None
        v = exp_from_counts(cts,pl)
        v2 = exp_v2(cts,pl)
        assert abs(v-v2)<1e-12
        E += c*v; details.append((base,c,v))
    return E, details
print("=== TRIPARTIÇÃO: E(θ) em Ha ===")
print(f"{'θ/π':>6} {'exato':>10} {'Aer(noise)':>11} {'hardware':>10} {'σ_hw':>7}")
rows=[]; a4_pass=0; a4_tot=0
grid=[t for t,_ in [(c["theta"],0) for c in ci["circuitos"]][::5]]
grid=sorted(set(round(t["theta"],6) for t in [ci["circuitos"][i] for i in range(0,30,5)]))
Eexact={round(t,6):e for t,e in ci["E_exact_grid"]}
res={}
for th in grid:
    Ehw,det = energy(th,"hw")
    Eaer,_  = energy(th,1)
    # A4: por circuito
    for base in ["Z","YXXY","YYXX","XXYY","XYYX"]:
        pl={q:ch for q,ch in enumerate(base)} if base!="Z" else {q:"Z" for q in range(4)}
        hwv=exp_from_counts(hw["counts"][idx[(th,base)]],pl)
        b1=exp_from_counts(refs[f"{th}|{base}"][0],pl); b2=exp_from_counts(refs[f"{th}|{base}"][1],pl)
        mid=(b1+b2)/2; sd=sigma_from_counts(hw["counts"][idx[(th,base)]],pl)
        z=abs(hwv-mid)/max(sd,1e-9)
        a4_tot+=1
        if z<=3.0: a4_pass+=1
    # σ energia (propagação simples)
    sig=0.0
    for tc in ci["termos"]:
        c=tc["c"]; pl={int(k):v for k,v in tc["pl"].items()}
        base="".join(pl.get(q,"I") for q in range(4))
        base="Z" if set(pl.values())<={"Z"} else base
        sig += (c*sigma_from_counts(hw["counts"][idx[(th,base)]],pl))**2
    sig=math.sqrt(sig)
    print(f"{th/math.pi:6.3f} {Eexact[th]:+10.6f} {Eaer:+11.6f} {Ehw:+10.6f} {sig:7.4f}")
    res[th]={"Ehw":round(Ehw,6),"Eaer":round(Eaer,6),"Eexact":Eexact[th],"sigma":round(sig,5)}
    rows.append((th,Ehw))
E0=ci["E0"]
Ehw_min=min(v["Ehw"] for v in res.values())
th_min=[t for t,v in res.items() if v["Ehw"]==Ehw_min][0]
print(f"\nA4 concordância por circuito (3σ da banda Aer): {a4_pass}/{a4_tot} {'PASS' if a4_pass>=24 else 'FAIL'}")
print(f"A5 VQE hardware: min grid E={Ehw_min:+.6f} Ha em θ={th_min:.4f} rad | FCI E0={E0:+.6f} Ha")
print(f"   desvio |E_hw−E0| = {abs(Ehw_min-E0):.4f} Ha (critério ≤0,20) {'PASS' if abs(Ehw_min-E0)<=0.20 else 'FAIL'}")
print(f"   variacional E_hw ≥ E0: {'PASS' if Ehw_min>=E0-0.05 else 'VIOLAÇÃO (reportada honestamente)'}")
# ajuste clássico A + B cosθ + C sinθ nos 6 pontos (otimizador de modelo, auditável)
ths=np.array([r[0] for r in rows]); Ehs=np.array([r[1] for r in rows])
Amat=np.c_[np.ones_like(ths),np.cos(ths),np.sin(ths)]
coef,*_=np.linalg.lstsq(Amat,Ehs,rcond=None)
fine=np.linspace(0,2*np.pi,2001)
Efit=coef[0]+coef[1]*np.cos(fine)+coef[2]*np.sin(fine)
print(f"Otimizador clássico (fit de modelo): θ*={fine[np.argmin(Efit)]:.4f} rad → E_VQE_hw≈{Efit.min():+.6f} Ha")
json.dump({"E0":E0,"por_theta":{str(k):v for k,v in res.items()},"A4":f"{a4_pass}/{a4_tot}",
           "Ehw_min":Ehw_min,"theta_min":th_min,"fit_theta":float(fine[np.argmin(Efit)]),
           "fit_E":float(Efit.min())},open(J("verify_002c6.json"),"w"),indent=1)
