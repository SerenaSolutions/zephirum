"""ZEPHIRUM live demo — Hugging Face Spaces (free CPU tier).
Runs the real interpreter via subprocess. SIMULATION MODE (CPU).
No vendor names; receipts and refusals kept honest."""
import gradio as gr, subprocess, sys, tempfile, os
CEFI = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cefirum")

SAMPLE = """# ZEPHIRUM — try me
print "hello from the quantum language"
bell = qpu_run("bell", 400)
print "entangled outcomes:", bell
print ai_ask("CHSH classical limit")
"""

def run_zephirum(code):
    fd, path = tempfile.mkstemp(suffix=".cef")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(code)
    try:
        p = subprocess.run(
            [sys.executable, os.path.join(CEFI, "cefirum.py"), "run", path],
            capture_output=True, text=True, cwd=CEFI, timeout=60)
        out = p.stdout
        if p.returncode != 0:
            out += ("\n" if out else "") + p.stderr[-800:]
        return out or "(no output)"
    finally:
        os.unlink(path)

with gr.Blocks(title="ZEPHIRUM — Quantum Language") as demo:
    gr.Markdown("# ZEPHIRUM — The Quantum Language")
    gr.Markdown("*Trivalent decisions (1 / 0 / REFUSED) with signed receipts. "
                "SIMULATION MODE on CPU — hardware receipts live in the main repo.*")
    with gr.Row():
        code_in = gr.Code(value=SAMPLE, label="ZEPHIRUM source (.cef)", lines=14)
        out = gr.Textbox(label="Output", lines=14)
    gr.Markdown("Builtins: `print` `qpu_run` (simulation) `ai_rag` `ai_qnn` `ai_ask` "
                "(trivalent gate). The gate refuses what it cannot ground.")
    gr.Markdown("Source: github.com/SerenaSolutions/zephirum — MIT")
    btn = gr.Button("Run ZEPHIRUM")
    btn.click(run_zephirum, inputs=code_in, outputs=out)

demo.launch()
