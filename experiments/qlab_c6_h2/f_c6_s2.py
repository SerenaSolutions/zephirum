# QLAB-002 C6 — ESTÁGIO 2: grade na região do mínimo proposta pelo otimizador
import ctypes as C, json, math, os, sys, time
import numpy as np
F=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(F)
def J(p): return os.path.join(F,p)
L=C.CDLL(os.path.join(ROOT,"libzyql.so"))
L.zyql_ir_reset.argtypes=[]; L.zyql_ir_h.argtypes=[C.c_int]; L.zyql_ir_x.argtypes=[C.c_int]
L.zyql_ir_cnot.argtypes=[C.c_int,C.c_int]; L.zyql_ir_measure.argtypes=[C.c_int]
L.zyql_ir_rx.argtypes=[C.c_int,C.c_double]; L.zyql_ir_rz.argtypes=[C.c_int,C.c_double]
L.zyql_ir_qasm3.argtypes=[C.c_char_p,C.c_size_t]
L.zyql_new.restype=C.c_void_p; L.zyql_free.argtypes=[C.c_void_p]
L.zyql_prove_claim.argtypes=[C.c_void_p,C.c_char_p]; L.zyql_mount.argtypes=[C.c_void_p,C.c_char_p,C.c_int]
L.zyql_dispatch_allowed.argtypes=[C.c_void_p,C.c_char_p,C.c_char_p]
def emit(theta,base):
    L.zyql_ir_reset(); L.zyql_ir_x(0); L.zyql_ir_x(1)
    L.zyql_ir_rx(3,math.pi/2); L.zyql_ir_rz(3,theta); L.zyql_ir_rx(3,-math.pi/2)
    L.zyql_ir_cnot(3,0); L.zyql_ir_cnot(3,1); L.zyql_ir_cnot(3,2)
    if base!="Z":
        for q,ch in enumerate(base):
            if ch=="X": L.zyql_ir_h(q)
            elif ch=="Y": L.zyql_ir_rz(q,-math.pi/2); L.zyql_ir_h(q)
    for q in range(4): L.zyql_ir_measure(q)
    b=C.create_string_buffer(8192); L.zyql_ir_qasm3(b,8192); return b.value.decode()
n=sys.argv[1] if len(sys.argv)>1 else ""
if n=="build":
    from qiskit import qasm3, transpile, QuantumCircuit
    from qiskit.quantum_info import Statevector
    pr=json.load(open(J("prereg_002c6_estagio2.json")))
    ci=json.load(open(J("circuitos_002c6.json")))
    # E exato nos pontos da grade 2 (do mesmo pipeline kernel compilado)
    def sv_of(theta):
        q=qasm3.loads(emit(theta,"Z")); q.remove_final_measurements(inplace=True); return Statevector(q).data
    import re
    from pennylane import qchem
    import pennylane as qml
    Hq,_=qchem.molecular_hamiltonian(["H","H"],qml.math.array([0,0,-0.6614,0,0,0.6614]),basis="sto-3g")
    cs,ws=Hq.terms()
    I2=np.eye(2); Xm=np.array([[0,1],[1,0]]); Ym=np.array([[0,-1j],[1j,0]]); Zm=np.diag([1,-1])
    Pm={'I':I2,'X':Xm,'Y':Ym,'Z':Zm}
    def op(s):
        m=np.array([[1.0]])
        for q in [3,2,1,0]: m=np.kron(m,Pm[s[q]])
        return m
    termos=[]
    for c,w in zip(cs,ws):
        s=str(w); pl={}
        for m2 in re.finditer(r"([XYZ])\((\d+)\)",s): pl[int(m2.group(2))]=m2.group(1)
        termos.append((float(c),pl,op("".join(pl.get(q,"I") for q in range(4)))))
    def energy(theta):
        v=sv_of(theta)
        return sum(c*float(np.real(np.vdot(v,M@v))) for c,pl,M in termos)
    Eex=[[round(t,6),round(energy(t),6)] for t in pr["grade_theta_rad"]]
    print("E exato na grade 2:", Eex)
    lay=ci["circuitos"][0]["layout"]
    circ=[{"theta":round(t,6),"base":b,"layout":lay,"qasm":emit(t,b)} for t in pr["grade_theta_rad"] for b in pr["bases"]]
    json.dump({"circuitos":circ,"E_exact_grid2":Eex},open(J("circuitos_002c6_s2.json"),"w"))
    print("circuitos estágio 2:",len(circ))
elif n=="refs":
    from qiskit import qasm3, transpile
    from qiskit_aer import AerSimulator
    from qiskit_aer.noise import NoiseModel
    from qiskit_ibm_runtime import QiskitRuntimeService
    ci=json.load(open(J("circuitos_002c6_s2.json")))
    svc=QiskitRuntimeService(channel="ibm_quantum_platform", token=os.environ["API_KEY"])
    be=svc.backend("ibm_fez"); nm=NoiseModel.from_backend(be)
    ref={}
    for c in ci["circuitos"]:
        tq=transpile(qasm3.loads(c["qasm"]),backend=be,initial_layout=c["layout"],optimization_level=0,seed_transpiler=11)
        outs=[]
        for s in [3,7]:
            outs.append(AerSimulator(noise_model=nm).run(tq,shots=1024,seed_simulator=s).result().get_counts())
        ref[f"{c['theta']}|{c['base']}"]=outs
    json.dump(ref,open(J("refs_002c6_s2.json"),"w")); print("refs Aer s2:",len(ref))
elif n=="submit":
    ci=json.load(open(J("circuitos_002c6_s2.json")))
    import hashlib
    cert={"prereg_s2":hashlib.sha256(open(J("prereg_002c6_estagio2.json"),'rb').read()).hexdigest(),
          "circs_s2":hashlib.sha256(open(J("circuitos_002c6_s2.json"),'rb').read()).hexdigest()}
    json.dump(cert,open(J("cert_002c6_s2.json"),"w"),indent=1)
    k=L.zyql_new(78)
    L.zyql_prove_claim(k,b"qlab-c6-h2-s2"); L.zyql_mount(k,b"/dev/qpu0",1)
    if L.zyql_dispatch_allowed(k,b"qlab-c6-h2-s2",b"/dev/qpu0")!=0: print("RECUSA DO KERNEL"); sys.exit(4)
    L.zyql_free(k)
    from qiskit import qasm3, transpile
    from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
    svc=QiskitRuntimeService(channel="ibm_quantum_platform", token=os.environ["API_KEY"])
    be=svc.backend("ibm_fez")
    tq=[transpile(qasm3.loads(c["qasm"]),backend=be,initial_layout=c["layout"],optimization_level=0,seed_transpiler=11) for c in ci["circuitos"]]
    job=SamplerV2(mode=be).run(tq,shots=1024)
    d={"job_id":job.job_id(),"shots":1024,"n":len(tq),"status":"SUBMITTED","submetido_em":time.strftime("%Y-%m-%d %H:%M:%S")}
    json.dump(d,open(J("hw_002c6_s2.json"),"w")); print("job s2:",job.job_id())
elif n=="collect":
    from qiskit_ibm_runtime import QiskitRuntimeService
    d=json.load(open(J("hw_002c6_s2.json")))
    svc=QiskitRuntimeService(channel="ibm_quantum_platform", token=os.environ["API_KEY"])
    job=svc.job(d["job_id"]); t0=time.time()
    while time.time()-t0<250:
        st=str(job.status())
        if st in ("DONE","ERROR","FAILED","CANCELLED"): break
        time.sleep(15)
    d["status"]=st; d["espera_s"]=round(time.time()-t0,1)
    if st=="DONE": d["counts"]=[job.result()[i].data.m.get_counts() for i in range(d["n"])]
    json.dump(d,open(J("hw_002c6_s2.json"),"w")); print("status s2:",st,"| counts:", "counts" in d)
