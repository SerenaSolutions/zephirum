# ZYQL S1 — MODELO DE AMEACAS E POLITICAS — kernel ZEPHYRUM 1.12
Estado: ESPECIFICACAO CONGELADA CANDIDATA (aguarda aprovacao do Diretor-Geral)
Principio: NEGACAO POR PADRAO. O que nao esta autorizado, esta proibido.
Meta: eliminar ambiguidade operacional — cada termo abaixo tem UMA definicao.

## 1. Ativos (o que se protege)

A1. Programas ZYQL e corpus de testemunhos (fonte e AST).
A2. Chaves: privadas ML-DSA-44 (assinatura), tokens de proxy da camada LLM.
A3. Recibos e pacotes de evidencias (cadeia, integridade, autenticidade).
A4. Credenciais do gateway de hardware quantico.
A5. Resultados cientificos e alegacoes publicas da casa (reputacao).

## 2. Adversarios e fontes de falha

T1. Programa nao confiavel: tenta ler/escrever fora do escopo, exceder
    recursos ou comunicar-se sem permissao.
T2. Atacante de replay: reutiliza recibo antigo ou assinatura valida
    em contexto novo.
T3. Falsificador: altera programa, politica ou recibo apos a assinatura.
T4. Observador externo: intercepta comunicacao (tokens, jobs, evidencias).
T5. Ambiente comprometido: sandbox ou runtime viciado produz evidencia falsa.
T6. Confused deputy: execucao autorizada e usada para fim nao autorizado.

## 3. Fronteiras de confianca

F1. Parser/compilador <-> runtime (contrato e tipo validados antes de rodar).
F2. Policy Gate <-> execucao (autorizacao decidida ANTES, recusada em caso negativo).
F3. Sandbox <-> sistema hospedeiro (arquivos, processos, rede, syscalls).
F4. Execucao local <-> gateway de hardware quantico (canal autorizado, NAO zero-I/O).
F5. Emissor de recibos <-> verificador independente (zyql-verify).

## 4. Taxonomia "zero I/O" (definicao unica por sigla; proibida a frase solta)

ZN — zero acesso a rede.
ZF — zero acesso arbitrario ao sistema de arquivos.
ZP — zero interacao com processos externos.
ZC — zero comunicacao externa durante a execucao.
    ZI-LOCAL = ZN + ZF + ZP + ZC (execucao classica local).
    GATEWAY-QPU = comunicacao BOUNDED: destino fixo autorizado,
    conteudo registrado, identificadores unicos por execucao.
    E PROIBIDO afirmar que GATEWAY-QPU tem zero-I/O.
    Estado atual do kernel C: ZI-LOCAL verificado por inspecao de
    simbolos na biblioteca compilada (sem chamadas de I/O linkadas);
    para o runtime completo, exige enforcement de SO + testes de escape.

## 5. Estados de conformidade (DISTINTOS do veredito cientifico)

POLICY_COMPLIANT    — a politica exigida foi validada e ha evidencia
                      suficiente de sua aplicacao.
EXECUTION_COMPLIANT — a execucao observada respeitou os limites definidos.
RECEIPT_VALID       — recibo, assinatura e encadeamento passaram na verificacao.
Honestidade obrigatoria: recibo valido NAO prova execucao segura;
ausencia de violacao registrada NAO prova ausencia de violacao.
A forca da conclusao depende do enforcement, da cobertura do monitor
e da confiabilidade do ambiente.

## 6. Camadas de isolamento (escolha por risco)

Camada A — isolamento logico: estado, contexto, identificadores e
           espaco de nomes proprios por execucao.
Camada B — sandbox de SO: namespaces/seccomp/controles de acesso,
           conforme disponivel e configurado.
Camada C — fronteira forte: VM ou limite equivalente para codigo nao
           confiavel ou alto risco.
Camada D — supervisao: consumo, acessos proibidos, tempo; encerramento
           no limite com evento registrado.
Regra: a camada declarada no recibo e' a camada EFETIVAMENTE aplicada,
       nunca a camada pretendida.

## 7. Recibo de seguranca (envelope unico, secoes obrigatorias)

Declaracao / Autorizacao / Enforcement / Observacao / Resultado /
Verificacao. Recibo PREVIO assinado antes da execucao; POSTERIOR
referencia o previo por hash. Anti-replay: execution_id unico,
numero de sequencia monotono por chave, recusa de duplicatas.

## 8. Politica inicial v1 (negacao por padrao)

P1. Toda execucao declara proposito, criterio, budget e backend alvo.
P2. Sem autorizacao explícita no Policy Gate, nao executa (REFUSED + recibo de recusa).
P3. Execucao classica local: exige ZI-LOCAL (ou camada declarada).
P4. Hardware quantico: exige GATEWAY-QPU autorizado, com canal e destino fixos.
P5. Chaves privadas nunca entram em artefato publico nem em programa.
P6. Recibos validos nao substituem evidencia de correcao (4 niveis independentes).

## 9. Testes adversariais de aprovacao (S4-S6)

R1 rede: conexao externa sob politica bloqueada -> bloqueada + evento registrado.
R2 arquivos: leitura/escrita fora do escopo -> negada pelo controle real.
R3 recursos: memoria/CPU/tempo excedidos -> encerramento com estado identificado.
R4 adulteracao: programa/politica/recibo alterados pos-assinatura -> divergencia detectada.
R5 autorizacao: credencial expirada/revogada/estranha -> execucao rejeitada.
Escopo honesto: os testes demonstram comportamento NAS configuracoes
avaliadas; nao provam ausencia universal de vulnerabilidades.

## 10. Criterio de aceitacao do S1

Ativos, adversarios, fronteiras, riscos e politica documentados e
revisados por executivo que nao seja o autor (secao 10 da ordem do CEO).
Nenhum controle e' aprovado por quem o implementou.
