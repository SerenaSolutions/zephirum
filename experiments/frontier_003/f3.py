# FRONTIER 003 — discriminação duração vs pulso (IR v4 delay)
import ctypes as C, json, hashlib, math, os, sys, time
import numpy as np
F=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(F)
def J(p): return os.path.join(F,p)
L=C.CDLL(os.path.join(ROOT,"libzyql.so"))
L.zyql_ir_reset.argtypes=[]; L.zyql_ir_h.argtypes=[C.c_int]
L.zyql_ir_x.argtypes=[C.c_int]; L.zyql_ir_cnot.argtypes=[C.c_int,C.c_int]
L.zyql_ir_measure.argtypes=[C.c_int]; L.zyql_ir_delay.argtypes=[C.c_int,C.c_longlong]
L.zyql_ir_qasm3.argtypes=[C.c_char_p,C.c_size_t]
L.zyql_new.restype=C.c_void_p; L.zyql_free.argtypes=[C.c_void_p]
L.zyql_prove_claim.argtypes=[C.c_void_p,C.c_char_p]
L.zyql_mount.argtypes=[C.c_void_p,C.c_char_p,C.c_int]
L.zyql_dispatch_allowed.argtypes=[C.c_void_p,C.c_char_p,C.c_char_p]
def emit(kind,unit=None,k=0,delay_ns=0):
    L.zyql_ir_reset(); L.zyql_ir_h(0); L.zyql_ir_cnot(0,1)
    if kind=="hh":
        for _ in range(2*k):  # k unidades HH = 2k portas H por qubit
            L.zyql_ir_h(0); L.zyql_ir_h(1)
    elif kind=="delay" and delay_ns>0:
        L.zyql_ir_delay(0,delay_ns); L.zyql_ir_delay(1,delay_ns)
    L.zyql_ir_measure(0); L.zyql_ir_measure(1)
    b=C.create_string_buffer(32768); L.zyql_ir_qasm3(b,32768)
    return b.value.decode()
def sha(p): return hashlib.sha256(open(p,"rb").read()).hexdigest()
n=sys.argv[1] if len(sys.argv)>1 else ""
def tqc_pulsos(tq):
    op=dict(tq.count_ops()); return int(op.get("sx",0)+op.get("x",0)+op.get("cx",0))

if n=="build":
    from qiskit import qasm3, transpile
    from qiskit_ibm_runtime import QiskitRuntimeService
    svc=QiskitRuntimeService(channel="ibm_quantum_platform", token=os.environ["API_KEY"])
    be=svc.backend("ibm_fez")
    t_bell=transpile(qasm3.loads(emit("plain")),backend=be,initial_layout=[9,10],optimization_level=0,seed_transpiler=11,scheduling_method="asap")
    t_hh8=transpile(qasm3.loads(emit("hh",k=8)),backend=be,initial_layout=[9,10],optimization_level=0,seed_transpiler=11,scheduling_method="asap")
    dt_ns=be.dt*1e9
    D=int(round((t_hh8.duration-t_bell.duration)*dt_ns))
    D2=D//2
    print(f"dt={dt_ns:.3f} ns | bell={t_bell.duration}dt hh8={t_hh8.duration}dt | D={D} ns (metade {D2})")
    ckt=[{"id":"bell_base","par":[9,10],"qasm":emit("plain")},
         {"id":"hh8","par":[9,10],"qasm":emit("hh",k=8)},
         {"id":"delay_full","par":[9,10],"qasm":emit("delay",delay_ns=D)},
         {"id":"delay_half","par":[9,10],"qasm":emit("delay",delay_ns=D2)},
         {"id":"bell_149","par":[149,148],"qasm":emit("plain")},
         {"id":"delay_149","par":[149,148],"qasm":emit("delay",delay_ns=D)}]
    json.dump({"circuitos":ckt,"D_ns":D,"D_half_ns":D2,"dt_ns":dt_ns,
               "dur_bell_dt":t_bell.duration,"dur_hh8_dt":t_hh8.duration},open(J("circuits_003.json"),"w"))
    for c in ckt: open(J(f"q3_{c['id']}.qasm3"),"w").write(c["qasm"])
    print("circuitos:",len(ckt),"| delay units:",D,"ns")
elif n=="refs":
    from qiskit import qasm3, transpile
    from qiskit_aer import AerSimulator
    from qiskit_aer.noise import NoiseModel
    from qiskit_ibm_runtime import QiskitRuntimeService
    ci=json.load(open(J("circuits_003.json")))
    svc=QiskitRuntimeService(channel="ibm_quantum_platform", token=os.environ["API_KEY"])
    be=svc.backend("ibm_fez"); nm=NoiseModel.from_backend(be)
    ref={}
    for c in ci["circuitos"]:
        tq=transpile(qasm3.loads(c["qasm"]),backend=be,initial_layout=c["par"],optimization_level=0,seed_transpiler=11)
        vals=[]
        for s in [3,7]:
            ct=AerSimulator(noise_model=nm).run(tq,shots=2048,seed_simulator=s).result().get_counts()
            tot=sum(ct.values())
            vals.append(sum(v*(1 if k.replace(" ","")[0]==k.replace(" ","")[1] else -1) for k,v in ct.items())/tot)
        ref[c["id"]]={"banda":[min(vals),max(vals)],"pulsos":tqc_pulsos(tq),"duracao_dt":tq.duration}
    json.dump(ref,open(J("refs_003.json"),"w"),indent=1)
    for k,v in ref.items(): print(f"{k:12s} banda=[{v['banda'][0]:+.4f},{v['banda'][1]:+.4f}] pulsos={v['pulsos']} dur={v['duracao_dt']}dt")
if n=="execute":
    ci=json.load(open(J("circuits_003.json")))
    cert={"hyp":sha(J("hypotheses_003.json")),"des":sha(J("design_003.json")),
          "circuits":[(c["id"],sha(J(f"q3_{c['id']}.qasm3"))) for c in ci["circuitos"]]}
    json.dump(cert,open(J("cert_003.json"),"w"),indent=1)
    k=L.zyql_new(555)
    L.zyql_prove_claim(k,b"frontier-003"); L.zyql_mount(k,b"/dev/qpu0",1)
    if L.zyql_dispatch_allowed(k,b"frontier-003",b"/dev/qpu0")!=0: print("RECUSA DO KERNEL"); sys.exit(4)
    L.zyql_free(k)
    from qiskit import qasm3, transpile
    from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
    svc=QiskitRuntimeService(channel="ibm_quantum_platform", token=os.environ["API_KEY"])
    be=svc.backend("ibm_fez")
    tot=2048*len(ci["circuitos"])
    if tot>16000: print("ORÇAMENTO EXCEDIDO"); sys.exit(5)
    tq=[transpile(qasm3.loads(c["qasm"]),backend=be,initial_layout=c["par"],optimization_level=0,seed_transpiler=11) for c in ci["circuitos"]]
    job=SamplerV2(mode=be).run(tq,shots=2048); jid=job.job_id()
    d={"job_id":jid,"shots":2048,"circuits":len(tq),"status":"SUBMITTED","submetido_em":time.strftime("%Y-%m-%d %H:%M:%S")}
    json.dump(d,open(J("hw3.json"),"w")); print("job:",jid,"| tiros:",tot)
    t0=time.time()
    while time.time()-t0<300:
        if str(job.status())=="DONE": break
        time.sleep(15)
    d["status"]=str(job.status()); d["espera_s"]=round(time.time()-t0,1)
    if d["status"]=="DONE": d["counts"]=[job.result()[i].data.m.get_counts() for i in range(len(tq))]
    json.dump(d,open(J("hw3.json"),"w")); print("status:",d["status"],"| espera:",d.get("espera_s"))
