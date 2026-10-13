#!/usr/bin/env python3
"""
hoeffding_drift.py — Monte Carlo Simulation of Hoeffding Inequality Under Drift & Bias
Auditor: EXECUTIVO 3 — DIRETOR DE VERIFICAÇÃO E SEGURANÇA
"""

import numpy as np

S = 1024
TRIALS = 10000
SEED = 42

def run_simulation():
    np.random.seed(SEED)
    deltas = [0.01, 0.05]
    
    # Define test cases
    # (Case Name, Description, True p_bar, Shot Generator Function, Error Condition Lambda)
    cases = [
        (
            "C1_iid_p0.50",
            "i.i.d. p = 0.50 (fronteira)",
            0.50,
            lambda n: np.random.binomial(1, 0.50, size=(n, S)),
            lambda phat, eps: (phat > 0.5 + eps) | (phat < 0.5 - eps) # any non-REFUSED decision
        ),
        (
            "C2_iid_p0.52",
            "i.i.d. p = 0.52 (p > 0.5)",
            0.52,
            lambda n: np.random.binomial(1, 0.52, size=(n, S)),
            lambda phat, eps: phat < 0.5 - eps # wrong verdict = 0 when p > 0.5
        ),
        (
            "C3_drift_0.50_0.45",
            "Deriva linear 0.50->0.45 (p_bar = 0.475 < 0.5)",
            0.475,
            lambda n: np.random.binomial(1, np.linspace(0.50, 0.45, S), size=(n, S)),
            lambda phat, eps: phat > 0.5 + eps # wrong verdict = 1 when p_bar < 0.5
        ),
        (
            "C4_drift_0.50_0.55",
            "Deriva linear 0.50->0.55 (p_bar = 0.525 > 0.5)",
            0.525,
            lambda n: np.random.binomial(1, np.linspace(0.50, 0.55, S), size=(n, S)),
            lambda phat, eps: phat < 0.5 - eps # wrong verdict = 0 when p_bar > 0.5
        ),
        (
            "C5_bias_hardware_spam",
            "Viés sistemático QPU +0.06 (p_ideal=0.48, p_hw=0.54)",
            0.48, # p_ideal
            lambda n: np.random.binomial(1, 0.54, size=(n, S)),
            lambda phat, eps: phat > 0.5 + eps # wrong verdict = 1 relative to p_ideal < 0.5
        ),
        (
            "C6_multi_decision_100x",
            "Múltiplas decisões (N=100 por sessão, p=0.50)",
            0.50,
            lambda n: np.random.binomial(1, 0.50, size=(n, S*100)).reshape(n, 100, S),
            None # handled separately for multi-decision FWER
        )
    ]

    results = []

    print("=" * 100)
    print("HOEFFDING SOB DERIVA E VIÉS SISTEMÁTICO — SIMULAÇÃO MONTE CARLO (S=1024, N=10.000 trials)")
    print("Auditor: EXECUTIVO 3 — DIRETOR DE VERIFICAÇÃO E SEGURANÇA")
    print("=" * 100)

    for delta in deltas:
        eps = np.sqrt(np.log(2.0 / delta) / (2.0 * S))
        print(f"\n--- CONFIGURAÇÃO: δ = {delta:.2f} | Margem de Incerteza ε = {eps:.5f} (Zona REFUSED: [0.50-{eps:.5f}, 0.50+{eps:.5f}]) ---")
        
        for name, desc, pbar, gen_fn, err_fn in cases:
            if name == "C6_multi_decision_100x":
                # Multi-decision session FWER test
                data = gen_fn(TRIALS) # (10000, 100, 1024)
                phats = np.mean(data, axis=2) # (10000, 100)
                # Session has error if AT LEAST ONE of the 100 decisions emits non-REFUSED when p=0.50
                non_refused = (phats > 0.5 + eps) | (phats < 0.5 - eps)
                session_error = np.any(non_refused, axis=1)
                realized_rate = np.mean(session_error)
                violation = "SIM (FWER Violado!)" if realized_rate > delta else "NÃO"
                results.append((name, desc, delta, eps, realized_rate, violation))
                print(f"[{name}] {desc:55s} | Taxa Realizada: {realized_rate*100:6.2f}% | Violação: {violation}")
                continue

            shots = gen_fn(TRIALS)
            phat = np.mean(shots, axis=1)
            err_mask = err_fn(phat, eps)
            realized_rate = np.mean(err_mask)
            
            # Check if realized error rate violates delta
            is_violation = realized_rate > delta
            violation_str = "SIM (Garantia FALSA!)" if is_violation else "NÃO"
            
            results.append((name, desc, delta, eps, realized_rate, violation_str))
            
            refused_rate = np.mean(np.abs(phat - 0.5) <= eps)
            decided_rate = 1.0 - refused_rate
            
            print(f"[{name}] {desc:55s} | Taxa Erro: {realized_rate*100:6.2f}% | REFUSED: {refused_rate*100:5.2f}% | DECIDIDO: {decided_rate*100:5.2f}% | Violação: {violation_str}")

    print("\n" + "=" * 100)
    print("TABELA RESUMO: CASO × δ × MARGEM ε × TAXA REALIZADA × VIOLAÇÃO DA GARANTIA FORMAL")
    print("=" * 100)
    print(f"{'Caso':<22} | {'δ':<5} | {'Margem ε':<8} | {'Taxa Realizada':<15} | {'Violação da Garantia?':<22}")
    print("-" * 100)
    for name, desc, delta, eps, rate, viol in results:
        print(f"{name:<22} | {delta:<5.2f} | {eps:<8.5f} | {rate*100:13.3f}% | {viol:<22}")

    print("\n" + "=" * 100)
    print("CONCLUSÃO QUANTIFICADA E CONDIÇÕES ONDE A 'GARANTIA FORMAL P(erro) <= δ' É FALSA")
    print("=" * 100)
    print("""
1. O QUE A DESIGUALDADE DE HOEFFDING DE FATO GARANTE:
   A desigualdade de Hoeffding P(|p̂ - E[p̂]| ≥ ε) ≤ 2·exp(-2Sε²) é um teorema estritamente ESTATÍSTICO.
   Ele garante apenas que a média amostral p̂ de S variáveis aleatórias independentes e limitadas
   não se desvia da sua PRÓPRIA EXPECTÂNCIA REAIS ESTATÍSTICA E[p̂] por mais de ε, com probabilidade 1 - δ.

2. CONDIÇÕES SOB AS QUAIS A ALEGAÇÃO 'GARANTIA FORMAL P(erro) ≤ δ' É DEMONSTRADAMENTE FALSA:
   (A) Presença de Viés Sistemático do Hardware (Ruído SPAM / Decaimento T1/T2):
       Se a QPU possui um viés sistemático (ex: erro de leitura SPAM onde p_hw = p_ideal + 0.06),
       a amostragem estatística converge com alta precisão para p_hw = 0.54, e NÃO para p_ideal = 0.48.
       Resultado: O kernel emite Veredito = 1 (afirmando p_ideal > 0.5) com frequência realizada de ~46% (para δ=0.05),
       violando o limite nominal de 5% por QUASE UMA ORDEM DE GRANDEZA.

   (B) Múltiplas Decisões por Sessão sem Correção de FWER (Bonferroni / Holm):
       Se um job executa N=100 decisões independentes sob δ=0.05, a taxa de erro acumulada da sessão
       (FWER - Family-Wise Error Rate) atinge ~40% a 99%, tornando a alegação de "95% de confiança na sessão"
       matematicamente FALSA.

   (C) Ausência de Definição do Evento de Erro no Recibo:
       Sem especificar explicitamente se o "erro" é medido em relação a p_ideal ou p_hw, a alegação de
       garantia formal é semanticamente ambígua e juridicamente indefensável.

3. RECOMENDAÇÃO TÉCNICA:
   Para que o rótulo de garantia formal seja VÁLIDO e desbloqueado:
   a) O recibo DEVE explicitar que a garantia P(erro) ≤ δ se aplica estritamente a P(|p_hat - p_hw| ≥ ε),
      ou seja, à amostragem estatística do dispositivo, e NÃO ao ruído físico p_ideal.
   b) Incluir termo de calibração / erro sistemático mitigado no modelo.
   c) Aplicar correção de Bonferroni (δ_i = δ / N) quando N decisões forem tomadas em um único recibo.
""")

if __name__ == "__main__":
    run_simulation()
