/* RECEIPT CHAIN battery — fixes the HIGH replay finding of the adversarial audit.
   Checks: (a) seal fields present, (b) tamper detected, (c) replay/reorder detected,
   (d) honest chain passes. */
#include "../zyql.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
static int fails=0;
static void expect(int cond,const char *what){
  printf("%s  %s\n",cond?"[OK]":"[FAIL]",what); if(!cond) fails++; }
int main(void){
  const char *PROG =
    "MODEL type=EXACT kernel=KEPLER_III check=1.0 op== thr=0.01 assumption=unit solar mass\n"
    "ASK purpose=\"research orbital statistics\" question=\"T^2=a^3 for a=1?\"\n"
    "DATA a=1.0\n";
  zyql_decision *d1=zyql_decide(PROG);
  const char *r1=strdup(zyql_receipt(d1));
  zyql_close(d1);
  zyql_decision *d2=zyql_decide(PROG);
  const char *r2=strdup(zyql_receipt(d2));
  zyql_close(d2);
  /* (a) fields */
  expect(strstr(r1,"\"NONCE\":\"") && strstr(r1,"\"TIMESTAMP_UTC\":\"")
         && strstr(r1,"\"SEQ\":") && strstr(r1,"\"PREV_HASH\":\"")
         && strstr(r1,"\"RECEIPT_HASH\":\""),
         "receipts carry NONCE, TIMESTAMP_UTC, SEQ, PREV_HASH, RECEIPT_HASH");
  /* different receipts have different nonces and increasing SEQ */
  expect(strstr(r1,"\"NONCE\":\"")!=strstr(r2,"\"NONCE\":\""),"two decisions -> distinct nonces");
  expect(zyql_verify_receipt(r1)==1 && zyql_verify_receipt(r2)==1,
         "verify accepts freshly sealed receipts");
  /* (b) tamper */
  char *tampered=malloc(strlen(r1)+8); strcpy(tampered,r1);
  { char *sq=strstr(tampered,"\"SEQ\":"); if(sq&&strlen(sq)>6) sq[6]=(sq[6]=='1')?'2':'1'; }
  expect(zyql_verify_receipt(tampered)==0,"tampered receipt REJECTED");
  free(tampered);
  /* (c) replay across a chain: same receipt twice -> SEQ not increasing */
  const char *chain_replay[2]={r1,r1};
  expect(zyql_verify_receipt_chain(chain_replay,2)==0,
         "replayed receipt in chain REJECTED (SEQ not increasing)");
  /* reorder */
  const char *chain_disorder[2]={r2,r1};
  expect(zyql_verify_receipt_chain(chain_disorder,2)==0,
         "reordered chain REJECTED (PREV_HASH broken)");
  /* (d) honest chain */
  const char *chain_ok[2]={r1,r2};
  expect(zyql_verify_receipt_chain(chain_ok,2)==1,
         "honest two-receipt chain ACCEPTED (linked hashes, rising SEQ)");
  free((void*)r1); free((void*)r2);
  printf("%s chain battery\n", fails? "FAILURES in":"ALL PASS —");
  return fails?1:0;
}
