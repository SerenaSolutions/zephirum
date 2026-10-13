import json, math, os
import numpy as np
F=os.path.dirname(os.path.abspath(__file__))
def J(p): return os.path.join(F,p)
ci=json.load(open(J("circuitos_002c6.json")))           # termos + E0
c2=json.load(open(J("circuitos_002c6_s2.json")))
hw=json.load(open(J("hw_002c6_s2.json")))
refs=json.load(open(J("refs_002c6_s2.json")))
s1=json.load(open(J("verify_002c6.json")))
idx={}
for i,c in enumerate(c2["circuitos"]): idx[(round(c["theta"],6),c["base"])]=i
def expv(counts,pl):
    N=sum(counts.values()); s=0.0
    for k,v in counts.items():
        e=1.0
        for q,ch in pl.items(): e*= (1-2*int(k.replace(" ","")[3-q]))
        s+=v*e
    return s/N
def sig(counts,pl):
    N=sum(counts.values()); m=expv(counts,pl); return math.sqrt(max(0.0,(1-m*m)/N))
def energy(th):
    E=0.0; sd=0.0
    for tc in ci["termos"]:
        c=tc["c"]; pl={int(k):v for k,v in tc["pl"].items()}
        base="".join(pl.get(q,"I") for q in range(4))
        base="Z" if set(pl.values())<={"Z"} else base
        cts=hw["counts"][idx[(th,base)]]
        E+=c*expv(cts,pl); sd+=(c*sig(cts,pl))**2
    return E, math.sqrt(sd)
a4p=0; a4t=0
Eex={t:e for t,e in c2["E_exact_grid2"]}
print("=== ESTÁGIO 2: E(θ) Ha (região do mínimo) ===")
print(f"{'θ':>8} {'exato':>10} {'hardware':>10} {'σ':>6}")
res={}
for th in sorted(Eex):
    E,sd=energy(th); res[th]=(E,sd)
    print(f"{th:8.4f} {Eex[th]:+10.6f} {E:+10.6f} {sd:6.4f}")
    for base in ["Z","YXXY","YYXX","XXYY","XYYX"]:
        pl={q:ch for q,ch in enumerate(base)} if base!="Z" else {q:"Z" for q in range(4)}
        hwv=expv(hw["counts"][idx[(th,base)]],pl)
        b=[expv(refs[f"{th}|{base}"][i],pl) for i in (0,1)]
        z=abs(hwv-np.mean(b))/max(sig(hw["counts"][idx[(th,base)]],pl),1e-9)
        a4t+=1; a4p+= (1 if z<=3 else 0)
E0=ci["E0"]
best=min(res,key=lambda t:res[t][0]); Ehw_min=res[best][0]; sd_min=res[best][1]
print(f"\nA4(s2) concordância 3σ banda Aer: {a4p}/{a4t}")
print(f"A5/s2 mínimo hardware: E={Ehw_min:+.6f}±{sd_min:.4f} Ha em θ={best:.4f} | E0={E0:+.6f}")
print(f"    desvio |E_hw−E0| = {abs(Ehw_min-E0):.4f} Ha (critério ≤0,20: {'PASS' if abs(Ehw_min-E0)<=0.20 else 'FAIL'})")
print(f"    variacional E_hw ≥ E0−2σ: {'PASS' if Ehw_min>=E0-2*sd_min else 'VIOLAÇÃO'}")
# A7: forma da curva — mínimo na região central da grade?
ths=np.array(sorted(res)); Es=np.array([res[t][0] for t in ths])
central=ths[np.argmin(Es)]
print(f"A7 forma: mínimo em θ={central:.4f} (região central 5.97-6.13: {'DENTRO' if 5.97<=central<=6.13 else 'FORA'})")
combinado={**{k:v["Ehw"] for k,v in s1["por_theta"].items()}, **{str(t):round(res[t][0],6) for t in res}}
json.dump({"por_theta_s2":{str(t):{"Ehw":round(res[t][0],6),"sigma":round(res[t][1],5),"Eexact":Eex[t]} for t in res},
           "A4_s2":f"{a4p}/{a4t}","Ehw_min_s2":round(Ehw_min,6),"theta_min_s2":best,
           "desvio_vs_E0":round(abs(Ehw_min-E0),4),"job":hw["job_id"]},open(J("verify_002c6_s2.json"),"w"),indent=1)
