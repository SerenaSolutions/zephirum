# FRONTIER 003 — VERIFY: regra de decisão pré-registrada
import json, math, os
import numpy as np
F=os.path.dirname(os.path.abspath(__file__))
def J(p): return os.path.join(F,p)
ci=json.load(open(J("circuits_003.json"))); hw=json.load(open(J("hw3.json"))); refs=json.load(open(J("refs_003.json")))
ids={c["id"]:i for i,c in enumerate(ci["circuitos"])}
ct={c["id"]:hw["counts"][i] for i,c in enumerate(ci["circuitos"])}
def zz(ct): 
    tot=sum(ct.values()); return sum(v*(1 if k.replace(" ","")[0]==k.replace(" ","")[1] else -1) for k,v in ct.items())/tot
def pe(ct):
    tot=sum(ct.values()); return sum(v for k,v in ct.items() if k.replace(" ","")[0]==k.replace(" ","")[1])/tot
def z2(c1,c2,n=2048):
    p1,p2=pe(c1),pe(c2); p=(p1+p2)/2
    return (p1-p2)/math.sqrt(p*(1-p)*(2/n))
rng=np.random.default_rng(3)
out={}
print(f"emparelhamento: D={ci['D_ns']} ns (hh8={ci['dur_hh8_dt']}dt vs bell+delay={ci['dur_bell_dt']}+{int(ci['D_ns']/ci['dt_ns'])}dt)")
for c in ci["circuitos"]:
    z=zz(ct[c["id"]]); arr=[(1 if k.replace(" ","")[0]==k.replace(" ","")[1] else -1) for k,v in ct[c["id"]].items() for _ in range(v)]
    bs=[float(np.mean(rng.choice(arr,len(arr)))) for _ in range(3000)]
    lo,hi=np.percentile(bs,[2.5,97.5])
    b=refs[c["id"]]["banda"]
    print(f"{c['id']:12s} ZZ={z:+.4f} IC[{lo:+.3f},{hi:+.3f}] modelo[{min(b):+.3f},{max(b):+.3f}] dentro={min(b)<=z<=max(b)}")
    out[c["id"]]={"zz":round(z,4),"ic95":[round(lo,4),round(hi,4)],"banda_modelo":b}
zb=z2(ct["delay_full"],ct["bell_base"]); zh=z2(ct["delay_full"],ct["hh8"])
zhalf=z2(ct["delay_half"],ct["bell_base"]); z149=z2(ct["delay_149"],ct["bell_149"])
print(f"\nPRIMÁRIA: z(delay vs bell)={zb:+.2f} | z(delay vs hh8)={zh:+.2f}")
print(f"SECUNDÁRIA: z(delay_half vs bell)={zhalf:+.2f} | replicação 149: z(delay_149 vs bell_149)={z149:+.2f}")
if abs(zb)<2.58 and zh>2.58: ver="H4_CONFIRMADA"
elif abs(zh)<2.58 and abs(zb)>2.58: ver="H2_CONFIRMADA"
else: ver="INCONCLUSIVO"
print("VEREDITO pré-registrado:",ver)
out["_decisao"]={"z_delay_vs_bell":round(zb,3),"z_delay_vs_hh8":round(zh,3),"z_half":round(zhalf,3),"z_149":round(z149,3),"veredito":ver}
json.dump(out,open(J("verify_003.json"),"w"),ensure_ascii=False,indent=1)
