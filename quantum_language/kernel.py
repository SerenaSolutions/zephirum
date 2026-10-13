# -*- coding: utf-8 -*-
"""
Zephyrum Kernel — hybrid classical/quantum supervisor.

Process table, qubit scheduler, and a syscall-style dispatch table,
in the spirit of the AUŠRA mission contract: every job gets an
audit record and a validation verdict.
"""

import time
import uuid

import qpu


class SyscallUnknown(RuntimeError):
    pass


class Job:
    def __init__(self, name, func, priority=5):
        self.id = uuid.uuid4().hex[:8]
        self.name = name
        self.func = func
        self.priority = priority
        self.status = "QUEUED"
        self.result = None
        self.started_at = None
        self.finished_at = None

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "status": self.status,
            "started": self.started_at, "finished": self.finished_at,
        }


class ZephyrumKernel:
    def __init__(self, backend="simulator"):
        self.backend = backend
        self.process_table = []
        self.audit_log = []
        self._syscalls = {
            "status": self._syscall_status,
            "run": self._syscall_run,
            "bell": self._syscall_bell,
            "ghz": self._syscall_ghz,
            "shutdown": self._syscall_shutdown,
        }
        self._log("kernel", "init", f"backend={backend}")

    # -- audit ---------------------------------------------------------
    def _log(self, actor, action, details):
        self.audit_log.append({
            "timestamp": time.time(), "actor": actor,
            "action": action, "details": details,
        })

    # -- scheduler -------------------------------------------------------
    def schedule(self, job):
        self.process_table.append(job)
        self._log("scheduler", "enqueue", f"{job.name}:{job.id} prio={job.priority}")
        # fidelity-first: execute immediately in prototype (priority respected
        # by sorting; a real time-sliced scheduler is Phase 2 work)
        order = sorted(self.process_table, key=lambda j: j.priority)
        while any(j.status == "QUEUED" for j in order):
            for j in order:
                if j.status != "QUEUED":
                    continue
                j.status = "RUNNING"
                j.started_at = time.time()
                self._log("scheduler", "dispatch", j.name)
                try:
                    j.result = j.func(self)
                    j.status = "DONE"
                except Exception as e:
                    j.result = {"error": str(e)}
                    j.status = "FAILED"
                j.finished_at = time.time()
                self._log("scheduler", "exit", f"{j.name}:{j.status}")
        return j.result

    # -- syscalls ---------------------------------------------------------
    def syscall(self, name, *args):
        if name not in self._syscalls:
            raise SyscallUnknown(f"unknown syscall '{name}'")
        self._log("process", "syscall", f"{name}({args})")
        return self._syscalls[name](*args)

    def _syscall_status(self):
        return {
            "version": "0.1.0-alpha", "backend": self.backend,
            "mode": qpu.SIMULATION_LABEL if self.backend == "simulator" else "live",
            "processes": [j.to_dict() for j in self.process_table],
        }

    def _syscall_run(self, circuit_name):
        """Run a named circuit program. Only programs registered in the
        program table are executable — nothing is invented at runtime."""
        from programs import PROGRAMS
        if circuit_name not in PROGRAMS:
            return {"error": f"program '{circuit_name}' not found"}
        n, build, shots = PROGRAMS[circuit_name]
        backend = qpu.acquire(n, self.backend)
        build(backend)
        import numpy as np
        counts = backend.sample(shots, np.random.default_rng(0x2E))  # seed: '.')
        self._log("qpu", "execute", f"{circuit_name} shots={shots} {qpu.SIMULATION_LABEL}")
        return {"counts": counts, "shots": shots, "backend": qpu.SIMULATION_LABEL}

    def _syscall_bell(self):
        return self.syscall("run", "bell")

    def _syscall_ghz(self):
        return self.syscall("run", "ghz")

    def _syscall_shutdown(self):
        self._log("kernel", "shutdown", "clean")
        return {"ok": True}
