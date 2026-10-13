#!/usr/bin/env python3
"""HOUSE INTELLIGENCE KERNEL — RAG layer (Retrieval-Augmented Grounding).
Pure-Python TF-IDF over the house corpus: signed receipts, Léo's manual, diary.
RULE: retrieval grounds the answer with citable receipt ids; it never decides.
"""
import json, math, os, re, sys

CORPUS_FILES = ["zyql_qutrit/receipts.jsonl", "leo_zyql_ravi/LEO_TECH.md", "leo_zyql_ravi/diary.md"]
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def chunks():
    docs = []
    for f in CORPUS_FILES:
        p = os.path.join(BASE, f)
        if not os.path.exists(p): continue
        if f.endswith(".jsonl"):
            for line in open(p):
                m = json.loads(line)
                pay = m.get("payload", {})
                if isinstance(pay, str):
                    import base64; pay = json.loads(base64.b64decode(pay))
                rid = pay.get("id") or pay.get("receipt_id") or "receipt"
                text = " ".join(str(v) for k, v in pay.items() if isinstance(v, (str, int, float)) and k != "public_key_b64")
                docs.append({"source": rid, "file": f, "text": text[:600]})
        else:
            for para in re.split(r"\n\s*\n", open(p).read()):
                if len(para.strip()) > 40: docs.append({"source": f"{os.path.basename(f)}#{para[:30]}", "file": f, "text": para[:600]})
    return docs

def tokenize(s): return re.findall(r"[a-zà-ÿ0-9]+", s.lower())

def tfidf(docs):
    tok = [tokenize(d["text"]) for d in docs]
    df = {}
    for t in tok:
        for w in set(t): df[w] = df.get(w, 0) + 1
    idf = {w: math.log(len(docs)/(1+n)) for w, n in df.items()}
    vecs = []
    for t in tok:
        v = {}
        for w in t: v[w] = v.get(w, 0) + 1
        for w in v: v[w] *= idf[w]
        vecs.append(v)
    return vecs, idf

def retrieve(query, k=3):
    docs = chunks(); vecs, idf = tfidf(docs)
    q = {}
    for w in tokenize(query): q[w] = q.get(w, 0) + 1
    q = {w: c * idf.get(w, 0.0) for w, c in q.items()}
    def score(v):
        dot = sum(min(q[w], v[w]) for w in q if w in v)
        nq = math.sqrt(sum(x*x for x in q.values())) or 1
        nv = math.sqrt(sum(x*x for x in v.values())) or 1
        return dot/(nq*nv)
    ranked = sorted(range(len(docs)), key=lambda i: score(vecs[i]), reverse=True)[:k]
    return [{"source": docs[i]["source"], "text": docs[i]["text"][:300],
             "score": round(score(vecs[i]), 4)} for i in ranked if score(vecs[i]) > 0]

if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "grover resultado qpu real difusor"
    print(f"QUERY: {q}\n")
    for r in retrieve(q):
        print(f"[{r['score']}] {r['source']}\n  {r['text'][:220]}\n")
