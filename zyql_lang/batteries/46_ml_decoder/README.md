# Bateria 46 — Decoder de IA auditado pela régua exata

Surface code d=3 (distância provada por enumeração) + três decodificadores medidos
EXAUSTIVAMENTE sobre os 262144 padrões de Pauli:

- L1 EXATO: líder de coset por enumeração — ótimo por construção sob ruído iid
- V2 NEURAL supervisionado (Adam, 30k amostras, p=0.01): 1,143× o ótimo
- V3 NEURAL por imitação do líder: razão exata 1,000 — iguala, nunca supera

Conclusão (FATO medido): nenhum decoder pode ter erro lógico abaixo do líder de
coset neste critério. O valor de um decoder neural é velocidade em códigos
grandes, não precisão acima do ótimo.

Recibo: RECEIPT_46.json (hash 4fde8169). Rótulos: EXATO= FATO; NEURAL = EXPERIMENTAL,
nunca certificável por instância.
