# QLAB-002 · C6 — H2 ponta a ponta em ZYQL (kernel IR → QASM3 → IBM)
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
    # ansatz (do h2.zeph): x0,x1; Ry(θ) em d=3 (via rx(π/2)·rz(θ)·rx(−π/2), máquina-verificado); CNOTs controle 3
    L.zyql_ir_reset(); L.zyql_ir_x(0); L.zyql_ir_x(1)
    L.zyql_ir_rx(3,math.pi/2); L.zyql_ir_rz(3,theta); L.zyql_ir_rx(3,-math.pi/2)
    L.zyql_ir_cnot(3,0); L.zyql_ir_cnot(3,1); L.zyql_ir_cnot(3,2)
    if base!="Z":
        for q,ch in enumerate(base):           # base por qubit: X→h; Y→rz(-π/2)+h
            if ch=="X": L.zyql_ir_h(q)
            elif ch=="Y": L.zyql_ir_rz(q,-math.pi/2); L.zyql_ir_h(q)
    for q in range(4): L.zyql_ir_measure(q)
    b=C.create_string_buffer(8192); L.zyql_ir_qasm3(b,8192); return b.value.decode()
def pauli_eig(key,q): return 1-2*int(key[3-q])   # qiskit: key = c3c2c1c0
n=sys.argv[1] if len(sys.argv)>1 else ""
if n=="build":
    from qiskit import qasm3, transpile, QuantumCircuit
    from qiskit.quantum_info import Statevector
    import pennylane as qml
    H=np.load(J(".." + "/qlab_c6_H.npy"))
    # A2: prova de compilação — estado preparado vs analítico
    theta=0.7
    qc=qasm3.loads(emit(theta,"Z")); qc.remove_final_measurements(inplace=True)
    sv=Statevector(qc).data
    tgt=np.zeros(16); a=theta/2
    tgt[int("0011",2)]=math.cos(a)   # q3q2q1q0 = 0011 → q0=q1=1 (HF)
    tgt[int("1100",2)]=math.sin(a)   # q3=q2=1 (duplamente excitado)
    fid=abs(np.vdot(tgt,sv))**2
    print(f"A2 fidelidade ansatz: {fid:.12f} {'PASS' if fid>1-1e-9 else 'FAIL'}")
    assert fid>1-1e-9
    # Ry-decomposição: prova de que Rx(π/2)Rz(θ)Rx(−π/2) = Ry(θ)
    print("A2 Ry-decomposição: coberta pela fidelidade analítica acima (estado completo já validado)")
    # curva local exata + A3
    def sv_of(theta):
        q=qasm3.loads(emit(theta,"Z")); q.remove_final_measurements(inplace=True); return Statevector(q).data
    ZZ=np.diag([1,-1,-1,1,-1,1,1,-1,-1,1,1,-1,1,-1,-1,1])  # Z0Z1 em ordem little-endian? computado abaixo genericamente
    def pauli_string_exp(sv,pl):  # pl ex: {0:'Z',1:'Z'}
        v=np.asarray(sv); dim=16
        e=0.0
        for i in range(dim):
            bits=[(i>>q)&1 for q in range(4)]
            s=1.0
            for q,p in pl.items():
                if p=="X": return None
                if p=="Z": s*=1-2*bits[q]
            e+=abs(v[i])**2*s
        return e
    # construir todos os 15 termos como matrizes
    I2=np.eye(2); X=np.array([[0,1],[1,0]]); Y=np.array([[0,-1j],[1j,0]]); Z=np.diag([1,-1])
    P={'I':I2,'X':X,'Y':Y,'Z':Z}
    def op(s):  # s='XY..'? wire 0 primeiro → little-endian: wire0 = bit menos significativo = fator mais à direita
    # qiskit statevector index i: bit q of i é qubit q → qubit 0 = menos significativo
    # matriz = kron(q3,q2,q1,q0)
        m=np.array([[1.0]])
        for q in [3,2,1,0]: m=np.kron(m,P[s[q]])
        return m
    TERMQ=[("I",""),("Z","ZIII"),("Z","IZII"),("ZZ","ZZII"),("Z","IIIZ"),("ZZ","ZIIZ"),("ZZ","IZZI"),
           ("YXXY","YXXY"),("YYXX","YYXX"),("XXYY","XXYY"),("XYYX","XYYX"),("ZZ","IIZZ"),("ZZ","ZIZI"),("ZZ","IZZI2")]
    # melhor: reconstruir termos do próprio H carregado
    from pennylane import qchem
    Hq,nq=qchem.molecular_hamiltonian(["H","H"],qml.math.array([0,0,-0.6614,0,0,0.6614]),basis="sto-3g")
    cs,ws=Hq.terms()
    termos=[]
    import re
    for c,w in zip(cs,ws):
        s=str(w); pl={}
        for m2 in re.finditer(r"([XYZ])\((\d+)\)", s): pl[int(m2.group(2))]=m2.group(1)
        termos.append((float(c),pl,op("".join(pl.get(q,"I") for q in range(4)))))
    def energy(theta,mode="exact"):
        v=sv_of(theta)
        if mode=="exact":
            return sum(c*float(np.real(np.vdot(v,M@v))) for c,pl,M in termos)
    th=np.linspace(0,2*math.pi,201)
    Es=[energy(t) for t in th]
    E0=float(np.linalg.eigvalsh(H)[0]); Emin=min(Es)
    print(f"A3 VQE local exato: min E={Emin:+.6f} Ha | FCI E0={E0:+.6f} Ha | gap={Emin-E0:.2e} Ha {'PASS' if Emin-E0<1e-3 else 'FAIL'}")
    assert Emin-E0<1e-3
    # layout linear no coupling map
    from qiskit_ibm_runtime import QiskitRuntimeService
    svc=QiskitRuntimeService(channel="ibm_quantum_platform", token=os.environ["API_KEY"])
    be=svc.backend("ibm_fez"); cm=[tuple(e) for e in be.coupling_map]
    nb={}; 
    for a,b in cm: nb.setdefault(a,set()).add(b); nb.setdefault(b,set()).add(a)
    def chain4():
        for s in sorted(nb):
            for m1 in sorted(nb[s]):
                for m2 in sorted(nb[m1]):
                    if m2 in (s,m1): continue
                    for m3 in sorted(nb[m2]):
                        if m3 in (s,m1,m2): continue
                        return [s,m1,m2,m3]
    lay=chain4(); print("layout físico:",lay)
    prereg=json.load(open(J("prereg_002c6.json")))
    circ=[]
    for thk in prereg["grade_theta_rad"]:
        for base in prereg["bases"]:
            circ.append({"theta":round(thk,6),"base":base,"layout":lay,"qasm":emit(thk,base)})
    json.dump({"circuitos":circ,"termos":[{"c":c,"pl":pl} for c,pl,M in termos],"E0":E0,
               "E_exact_grid":[[round(t,6),round(energy(t),6)] for t in prereg["grade_theta_rad"]]},
              open(J("circuitos_002c6.json"),"w"))
    print("circuitos compilados:",len(circ),"| E0:",round(E0,6))
elif n=="refs":
    from qiskit import qasm3, transpile
    from qiskit_aer import AerSimulator
    from qiskit_aer.noise import NoiseModel
    from qiskit_ibm_runtime import QiskitRuntimeService
    ci=json.load(open(J("circuitos_002c6.json")))
    svc=QiskitRuntimeService(channel="ibm_quantum_platform", token=os.environ["API_KEY"])
    be=svc.backend("ibm_fez"); nm=NoiseModel.from_backend(be)
    ref={}
    for c in ci["circuitos"]:
        tq=transpile(qasm3.loads(c["qasm"]),backend=be,initial_layout=c["layout"],optimization_level=0,seed_transpiler=11)
        outs=[]
        for s in [3,7]:
            ct=AerSimulator(noise_model=nm).run(tq,shots=1024,seed_simulator=s).result().get_counts()
            outs.append({k:v for k,v in ct.items()})
        ref[f"{c['theta']}|{c['base']}"]=outs
    json.dump(ref,open(J("refs_002c6.json"),"w"))
    print("refs Aer:",len(ref))
elif n=="execute":
    ci=json.load(open(J("circuitos_002c6.json")))
    import hashlib
    cert={"prereg":hashlib.sha256(open(J("prereg_002c6.json"),'rb').read()).hexdigest(),
          "zeph":hashlib.sha256(open(J("h2.zeph"),'rb').read()).hexdigest(),
          "circs":hashlib.sha256(open(J("circuitos_002c6.json"),'rb').read()).hexdigest()}
    json.dump(cert,open(J("cert_002c6.json"),"w"),indent=1)
    k=L.zyql_new(77)
    L.zyql_prove_claim(k,b"qlab-c6-h2"); L.zyql_mount(k,b"/dev/qpu0",1)
    if L.zyql_dispatch_allowed(k,b"qlab-c6-h2",b"/dev/qpu0")!=0: print("RECUSA DO KERNEL"); sys.exit(4)
    L.zyql_free(k)
    from qiskit import qasm3, transpile
    from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
    svc=QiskitRuntimeService(channel="ibm_quantum_platform", token=os.environ["API_KEY"])
    be=svc.backend("ibm_fez")
    tot=1024*len(ci["circuitos"])
    if tot>32000: print("ORÇAMENTO EXCEDIDO:",tot); sys.exit(5)
    tq=[transpile(qasm3.loads(c["qasm"]),backend=be,initial_layout=c["layout"],optimization_level=0,seed_transpiler=11) for c in ci["circuitos"]]
    job=SamplerV2(mode=be).run(tq,shots=1024); jid=job.job_id()
    d={"job_id":jid,"shots":1024,"n":len(tq),"status":"SUBMITTED","submetido_em":time.strftime("%Y-%m-%d %H:%M:%S")}
    json.dump(d,open(J("hw_002c6.json"),"w")); print("job:",jid,"| tiros:",tot)
    t0=time.time()
    while time.time()-t0<420:
        if str(job.status()) in ("DONE","ERROR","FAILED","CANCELLED"): break
        time.sleep(20)
    d["status"]=str(job.status()); d["espera_s"]=round(time.time()-t0,1)
    if d["status"]=="DONE": d["counts"]=[job.result()[i].data.m.get_counts() for i in range(len(tq))]
    json.dump(d,open(J("hw_002c6.json"),"w")); print("status:",d["status"],"| espera:",d.get("espera_s"))
