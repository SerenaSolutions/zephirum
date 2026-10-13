# AUDITORIA ADVERSARIAL DA ALEGAÇÃO "ZERO I/O NA FASE 2"
**Auditor:** EXECUTIVO 3 — DIRETOR DE VERIFICAÇÃO E SEGURANÇA (Projeto ZEPHIRUM / ZYQL — Serena Solutions)  
**Data:** 12/10/2026  
**Alvos:** `/tmp/zeph_repo/c-api/zyql.c` (c-api do repo) e `/app/conversations/6a89df0012b12b33001c5066/zyql_c_api.c` (kernel Solene).

---

## 1. PARECER E RESUMO EXECUTIVO

| Item Auditado | Diagnóstico Direto | Classificação de Maturidade | Severidade do Achado |
|---|---|---|---|
| **Alegação "Zero I/O na Fase 2"** | **NÃO É UMA PROPRIEDADE IMPOSTA, É APENAS UM COMENTÁRIO/DECLARAÇÃO.** Não há imposição por sandbox, seccomp, namespace ou separação de processos. | **BLOQUEADO como alegação formal** (IMPLEMENTADO apenas como ausência de chamadas I/O voluntárias no C). | **ALTA** |

---

## 2. INSPEÇÃO DE SÍMBOLOS DENTRO DAS APLICAÇÕES C (`nm` / `objdump`)

Os arquivos C foram compilados para arquivos objeto `.o` e inspecionados para identificar todos os símbolos da C Runtime Library (`libc`) importados pelos kernels:

### Comando Executado:
```bash
gcc -O2 -c /tmp/zeph_repo/c-api/zyql.c -o /tmp/zyql_repo.o
gcc -O2 -c /app/conversations/6a89df0012b12b33001c5066/zyql_c_api.c -o /tmp/zyql_solene.o

nm -u /tmp/zyql_repo.o
nm -u /tmp/zyql_solene.o
```

### Saída dos Símbolos Indefinidos (Importados da libc):

#### 1) Kernel do Repo Público (`c-api/zyql.c`):
```text
                 U exit
                 U free
                 U malloc
                 U realloc
                 U snprintf
                 U sprintf
                 U vsnprintf
```

#### 2) Kernel da Solene (`zyql_c_api.c`):
```text
                 U calloc
                 U free
                 U snprintf
                 U vsnprintf
```

### Análise dos Símbolos:
- **Símbolos de Rede / File I/O Ausentes:** Não existem símbolos como `fopen`, `open`, `read`, `write`, `socket`, `connect`, `send` ou `recv` explicitamente vinculados em nenhum dos dois módulos C.
- **Uso de Formatação de String em Memória:** As chamadas `snprintf`/`vsnprintf`/`sprintf` são utilizadas exclusivamente para construir o JSON de recibo em buffers alocados na memória (`sb_add` em `zyql.c`) e escrever no buffer de log interno (`klog` em `zyql_c_api.c`).

---

## 3. FUNDAMENTAÇÃO TÉCNICA: COMENTÁRIO VS PROPRIEDADE IMPOSTA

Embora os arquivos `.c` atualmente não chamem funções de E/S em arquivo ou rede, **a alegação "Zero I/O na Fase 2" é atualmente um mero COMENTÁRIO em documentação e NÃO uma propriedade arquiteturalmente garantida**.

### Por que NÃO é uma propriedade imposta:
1. **Ausência de Isolamento do SO (Seccomp / Landlock / Namespaces):**
   Nem o `zyql.c` nem o `zyql_c_api.c` utilizam filtros BPF de chamadas do sistema (`seccomp(2)`), `prctl(PR_SET_NO_NEW_PRIVS)` ou namespaces de rede/sistema de arquivos do Linux. O processo que executa a Fase 2 roda com permissões completas de usuário do sistema operacional.
2. **Monolito de Processo (Sem Process Split):**
   A Fase 0 (análise de propósito / portão) e a Fase 2 (execução do circuito / modelo) rodam exatamente no mesmo espaço de endereçamento de memória do mesmo processo.
3. **Injeção Potencial via Plugins / FFI:**
   Caso o motor execute extensões em C, Python ou Lua via FFI, qualquer código de terceiros executado na Fase 2 pode invocar `open()`, `socket()` ou `system()` impunemente sem ser bloqueado pelo kernel ZYQL.
4. **Ausência de Teste Negativo na Bateria:**
   Não há no repositório qualquer teste unitário negativo que tente realizar uma chamada de rede ou E/S durante a Fase 2 para provar que ela é abortada com `SIGSYS` ou erro de sandbox.

---

## 4. O QUE FALTA PARA TRANSFORMAR EM PROPRIEDADE IMPOSTA (REQUISITOS MÍNIMOS)

Para que o Diretor de Verificação e Segurança possa DESBLOQUEAR o rótulo de "Zero I/O na Fase 2" de **BLOQUEADO** para **IMPLEMENTADO**, a equipe de arquitetura e engenharia deve implementar:

1. **Separação de Módulo e Processo (Module Split):**
   Isolar o executor da Fase 2 em um processo filho dedicado (`zyql-exec-worker`), comunicando-se com o orquestrador apenas via um pipe unidirecional de memória/FD restrito.
2. **Filtro Seccomp Estrito no Worker (Kernel Linux):**
   Antes de iniciar a execução da Fase 2, o worker deve aplicar um filtro seccomp rígido:
   ```c
   // Permitir apenas SYS_read (no pipe), SYS_write (no pipe), SYS_exit_group, SYS_brk/mmap
   // Bloquear explicitamente SYS_socket, SYS_connect, SYS_openat, SYS_execve
   seccomp_rule_add(ctx, SCMP_ACT_KILL, SCMP_SYS(socket), 0);
   seccomp_rule_add(ctx, SCMP_ACT_KILL, SCMP_SYS(openat), 0);
   ```
3. **Bateria de Teste Negativo (`test_zero_io_negative.c`):**
   Criar um teste adversárial que injeta uma tentativa de escrita em disco/abertura de socket dentro do worker da Fase 2 e valida que o processo é imediatamente exterminado pelo SO com sinal `SIGSYS`.
