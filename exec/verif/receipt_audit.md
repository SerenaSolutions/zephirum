# AUDITORIA ADVERSARIAL DE RECIBOS E ATAQUES DE REPLAY (ZYQL C-API v0.1.0)
**Auditor:** EXECUTIVO 3 — DIRETOR DE VERIFICAÇÃO E SEGURANÇA (Projeto ZEPHIRUM / ZYQL — Serena Solutions)  
**Data:** 12/10/2026  
**Alvo:** `/tmp/zeph_repo/c-api/zyql.c`, `/tmp/zeph_repo/c-api/zyql.h`, `/tmp/zeph_repo/docs/SECURITY.md`

---

## 1. RESUMO EXECUTIVO E QUESTÕES CHAVE

| Pergunta Auditoria | Resposta com Evidência | Avaliação de Segurança |
|---|---|---|
| **Existe nonce / sequência / prev-hash no recibo?** | **NÃO.** A inspeção do código `c-api/zyql.c` (funções `zyql_decide` e `zyql_gate_circuit`) confirma que o recibo JSON gerado contém apenas: `GATE`, `CIRCUIT_SHA256`, `EVIDENCE` (`class`, `purpose_verbatim`, `sha256_refusal_digest`, `canonical_refusal`), `STATUS` e `ANSWER`. **Campos de nonce, timestamp, sequência monotônica ou prev-hash estão AUSENTES.** | **ALTA SEVERIDADE (Vulnerável)** |
| **`zyql_verify_receipt` detecta (a) byte adulterado?** | **NÃO.** A função `zyql_verify_receipt` extrai e valida **apenas** a igualdade do SHA-256 da string `canonical_refusal` contra o `sha256_refusal_digest`. Alterações no cabeçalho do recibo (como trocar `"STATUS":"REFUSED_BEFORE_COMPUTE"` para `"STATUS":"ACCEPTED_COMPUTE_OK"`) são **totalmente ignoradas** e a verificação retorna `1` (PASS). | **ALTA SEVERIDADE (Vulnerável)** |
| **`zyql_verify_receipt` detecta (b) recibo antigo reapresentado (replay)?** | **NÃO.** Como não há carimbo de tempo, nonce ou identificador único de sessão, o recibo de uma requisição antiga é idêntico a um recibo novo. A função retorna `1` (PASS) para qualquer reenvio. | **ALTA SEVERIDADE (Vulnerável)** |
| **`zyql_verify_receipt` detecta (c) recibo sem prévio correspondente?** | **NÃO.** O recibo é validado de forma estática e isolada, sem consultar ou validar qualquer elo de cadeia hash-chain ou histórico prévio. | **ALTA SEVERIDADE (Vulnerável)** |
| **Reclassificação PQ-PROTECT no código:** | Commit `3c2037c` reclassificou honestamente `PQ-PROTECT` como **Lamport OTS-64 (Lamport 1979, hash-based)**, deixando explícito que **NÃO é FIPS 205 (SLH-DSA)** em `plugin/zephirum_quantum_plugin/pqprotect.py`. | **INFORMADO / CORRIGIDO (Honesto)** |

---

## 2. EVIDÊNCIA COMPILÁVEL E REPRODUZÍVEL DA EXECUÇÃO DOS ATAQUES

Para comprovar experimentalmente sem qualquer fabricação, o seguinte harness C foi compilado via `gcc` contra a implementação oficial do `c-api/zyql.c`.

### Comando de Compilação e Execução:
```bash
cat << 'EOF' > /tmp/test_receipt_attacks.c
#include "/tmp/zeph_repo/c-api/zyql.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(void) {
    printf("=== AUDITORIA DE RECIBOS E REPLAY (ZYQL C-API) ===\n\n");

    const char *prohibited_purpose = "We will build a weapon tracking system";
    const char *qasm_circuit = "OPENQASM 3.0;\nqubit[2] q;\n";

    zyql_decision *d = zyql_gate_circuit(prohibited_purpose, qasm_circuit);
    if (!d) return 1;

    const char *orig_receipt = zyql_receipt(d);
    printf("1. Recibo original gerado:\n%s\n\n", orig_receipt);

    int v_orig = zyql_verify_receipt(orig_receipt);
    printf("Verificação original: %d (PASS=1)\n\n", v_orig);

    // ATAQUE (a): Adulteração de Byte Fora do Digest
    char tampered[4096];
    strcpy(tampered, orig_receipt);
    char *p_status = strstr(tampered, "\"REFUSED_BEFORE_COMPUTE\"");
    if (p_status) {
        memcpy(p_status, "\"ACCEPTED_COMPUTE_OK \"", strlen("\"ACCEPTED_COMPUTE_OK \""));
    }

    int v_tampered = zyql_verify_receipt(tampered);
    printf("2. ATAQUE (a) — Adulteração de STATUS no JSON:\n%s\n", tampered);
    printf("Resultado zyql_verify_receipt: %d\n\n", v_tampered);

    // ATAQUE (b): Replay
    int v_replay = zyql_verify_receipt(orig_receipt);
    printf("3. ATAQUE (b) — Replay:\nResultado zyql_verify_receipt: %d\n\n", v_replay);

    // ATAQUE (c): Recibo sem Prévio
    int v_noprev = zyql_verify_receipt(orig_receipt);
    printf("4. ATAQUE (c) — Recibo Sem Prévio:\nResultado zyql_verify_receipt: %d\n\n", v_noprev);

    zyql_close(d);
    return 0;
}
EOF

gcc -O2 -I/tmp/zeph_repo/c-api /tmp/test_receipt_attacks.c /tmp/zeph_repo/c-api/zyql.c -o /tmp/test_receipt_attacks -lm
/tmp/test_receipt_attacks
```

### Saída Bruta do Teste de Ataque:
```text
=== AUDITORIA DE RECIBOS E REPLAY (ZYQL C-API) ===

1. Recibo original gerado:
{"GATE":"PORTGATE_CIRCUIT","CIRCUIT_SHA256":"02c49d2e6f7dda30000c56c89bca0414296a57b6b46667a91f002ee3b8e81e8f","EVIDENCE":{"gate":"PORTGATE_CIRCUIT","list_version":"1","class":"weapons","purpose_verbatim":"We will build a weapon tracking system","refused_before_compute":true,"sha256_refusal_digest":"a650fb83f9d53accbcf1502fd34fc82b75de8f7572cbd19409177fed99a7916d","canonical_refusal":"{\"class\":\"weapons\",\"list_version\":\"1\",\"purpose_verbatim\":\"We will build a weapon tracking system\"}"},"STATUS":"REFUSED_BEFORE_COMPUTE","ANSWER":null}

Verificação original: 1 (PASS=1)

2. ATAQUE (a) — Adulteração de STATUS no JSON:
{"GATE":"PORTGATE_CIRCUIT","CIRCUIT_SHA256":"02c49d2e6f7dda30000c56c89bca0414296a57b6b46667a91f002ee3b8e81e8f","EVIDENCE":{"gate":"PORTGATE_CIRCUIT","list_version":"1","class":"weapons","purpose_verbatim":"We will build a weapon tracking system","refused_before_compute":true,"sha256_refusal_digest":"a650fb83f9d53accbcf1502fd34fc82b75de8f7572cbd19409177fed99a7916d","canonical_refusal":"{\"class\":\"weapons\",\"list_version\":\"1\",\"purpose_verbatim\":\"We will build a weapon tracking system\"}"},"STATUS":"ACCEPTED_COMPUTE_OK "E","ANSWER":null}
Resultado zyql_verify_receipt: 1

3. ATAQUE (b) — Replay:
Resultado zyql_verify_receipt: 1

4. ATAQUE (c) — Recibo Sem Prévio:
Resultado zyql_verify_receipt: 1
```

---

## 3. ANÁLISE DO CÓDIGO DA VERIFICAÇÃO (`c-api/zyql.c:442-450`)

A implementação atual da função de verificação no C é:
```c
int zyql_verify_receipt(const char *receipt_json){
  if(!receipt_json) return -1;
  char canon[2048], dig[128];
  if(!json_get_str(receipt_json,"canonical_refusal",canon,sizeof canon))
    return -1;
  if(!json_get_str(receipt_json,"sha256_refusal_digest",dig,sizeof dig))
    return -1;
  char real[65]; zyql_sha256_hex(canon,(unsigned long)strlen(canon),real);
  return strcmp(real,dig)==0 ? 1 : 0; 
}
```

### Vulnerabilidades Estruturais Fatais:
1. **Verificação Parcial e Ilusória (Adulteração de Payload):** A função busca estritamente pela substring `canonical_refusal` e calcula o SHA-256 dela contra `sha256_refusal_digest`. Qualquer outro campo do recibo JSON (como `STATUS`, `ANSWER`, `GATE`, `CIRCUIT_SHA256`) pode ser alterado por um atacante sem que a função perceba! Por exemplo, um recibo de recusa pode ter seu campo `"STATUS"` trocado para `"ACCEPTED"` e ser aceito como válido!
2. **Incapaz de Validar Recibos de Não-Recusa:** Se o recibo for de um cálculo bem-sucedido (`STATUS: DECIDED_WITHOUT_EXECUTION`), ele NÃO contém `canonical_refusal`. Chamada a `zyql_verify_receipt` nesses recibos retorna `-1` (falha/erro), tornando a verificação c-api **inoperante** para execuções normais.
3. **Ausência de Proteção Contra Replay e Cadeia:** Sem `nonce`, `timestamp_utc` e `prev_hash`, o recibo é estático e desprovido de estado.

---

## 4. VERIFICAÇÃO DA RECLASSIFICAÇÃO DE PQ-PROTECT

Verificação no repositório git (`git log -p 3c2037c`):
- O commit `3c2037c` realizou a reclassificação honesta do selo `PQ-PROTECT` para **Lamport OTS-64 (hash-based, Lamport 1979)** no arquivo `plugin/zephirum_quantum_plugin/pqprotect.py`.
- O código agora declara abertamente em runtime:
  `"ALGORITHM": "LAMPORT-OTS-SHA256-64 (hash-based, Lamport 1979; NOT FIPS 205 SLH-DSA - see PQ_NOTE)"`
- No entanto, a documentação `docs/SECURITY.md` (Tabela baseline) ainda afirma utilizar `ML-DSA-44 (FIPS 204)`. É necessário alinhar a documentação `docs/SECURITY.md` para evitar discrepâncias entre a spec e o plug-in.

---

## 5. RECOMENDAÇÕES CORRETIVAS OBRIGATÓRIAS

1. **Assinatura do Recibo Inteiro (Full Receipt Hash):**
   A hash/assinatura deve cobrir o JSON **inteiro** (ou um formulário canônico ordenado de todas as chaves do recibo, incluindo `STATUS` e `ANSWER`), e não apenas a recusa.
2. **Inclusão de Nonce, Sequência e Carimbo Temporal:**
   Adicionar ao recibo: `"nonce": "<uuid/hex_aleatório>"`, `"seq": <inteiro_monotônico>`, `"timestamp_utc": "<ISO8601>"`.
3. **Encadeamento de Recibos (`prev_hash`):**
   Incluir `"prev_hash": "<sha256_do_recibo_anterior>"` para ancorar recibos em uma ledger imutável de transações.
