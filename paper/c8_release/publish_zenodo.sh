#!/bin/bash
# Publica no Zenodo via API. Requer: export ZENODO_TOKEN=<token com deposit:write e deposit:actions>
set -e
API=https://zenodo.org/api/deposit/depositions
# 1) cria depósito vazio
DEP=$(curl -s -X POST "$API" -H "Authorization: Bearer $ZENODO_TOKEN" -H "Content-Type: application/json" -d '{}')
DEP_ID=$(echo "$DEP" | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])")
echo "deposito: $DEP_ID"
# 2) sobe arquivos
for F in ZYQL_preprint_v1.pdf zyql_artifacts_v1.zip main.tex zenodo_metadata.json; do
  BUCKET=$(curl -s "$API/$DEP_ID" -H "Authorization: Bearer $ZENODO_TOKEN" | python3 -c "import json,sys; print(json.load(sys.stdin)['links']['bucket'])")
  curl -s -X POST "$BUCKET/$F" -H "Authorization: Bearer $ZENODO_TOKEN" -F "file=@$F" > /dev/null
done
# 3) metadados
curl -s -X PUT "$API/$DEP_ID" -H "Authorization: Bearer $ZENODO_TOKEN" -H "Content-Type: application/json" -d @zenodo_metadata.json > /dev/null
# 4) PUBLICA (ação irreversível — gera DOI)
curl -s -X POST "$API/$DEP_ID/actions/publish" -H "Authorization: Bearer $ZENODO_TOKEN" | python3 -c "import json,sys; d=json.load(sys.stdin); print('DOI:', d.get('doi')); print('URL:', d.get('links',{}).get('html'))"
