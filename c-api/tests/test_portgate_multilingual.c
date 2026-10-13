/* PORTGATE multilingual battery: the safety gate must not be bypassed
   by writing a prohibited purpose in Portuguese/Spanish. */
#include "../zyql.h"
#include <stdio.h>
#include <string.h>
static int fails=0;
static void expect(int cond,const char *what){
  printf("%s  %s\n",cond?"[OK]":"[FAIL]",what); if(!cond) fails++; }
int main(void){
  const char *PROG_HEAD =
    "MODEL:\n    type: exact\n    check: kepler3\n    semi_major_axis_au: 5.204\n";
  const char *bad_pt = "ASK:\n    purpose: cometer fraude com notas falsificadas\n    question: x?\n";
  const char *bad_es = "ASK:\n    purpose: espionaje y vigilancia ilegal\n    question: x?\n";
  const char *good_pt = "ASK:\n    purpose: pesquisa orbital estatistica\n    question: x?\n";
  char prog[512];
  /* Portuguese prohibited purpose must REFUSE before compute */
  snprintf(prog,sizeof prog,"%s%s",PROG_HEAD,bad_pt);
  zyql_decision *r1=zyql_decide(prog);
  expect(zyql_result(r1)==ZYQL_REFUSED && strstr(zyql_receipt(r1),"REFUSED_BEFORE_COMPUTE"),
    "proposito proibido em PORTUGUES (fraude) e recusado antes do compute");
  zyql_close(r1);
  /* Spanish prohibited purpose must REFUSE */
  snprintf(prog,sizeof prog,"%s%s",PROG_HEAD,bad_es);
  zyql_decision *r2=zyql_decide(prog);
  expect(zyql_result(r2)==ZYQL_REFUSED && strstr(zyql_receipt(r2),"REFUSED_BEFORE_COMPUTE"),
    "proposito proibido em ESPANHOL (vigilancia) e recusado antes do compute");
  zyql_close(r2);
  /* Honest Portuguese research purpose must NOT be blocked */
  snprintf(prog,sizeof prog,"%s%s",PROG_HEAD,good_pt);
  zyql_decision *r3=zyql_decide(prog);
  const char *rc=zyql_receipt(r3);
  expect(!strstr(rc,"REFUSED_BEFORE_COMPUTE"),
    "pesquisa honesta em portugues NAO e bloqueada pela barreira de idioma");
  zyql_close(r3);
  printf("%s multilingual portgate battery\n", fails?"FAILURES in":"ALL PASS -");
  return fails?1:0;
}
