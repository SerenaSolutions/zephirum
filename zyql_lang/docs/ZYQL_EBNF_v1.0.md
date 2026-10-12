# ZYQL v1.0 — GRAMATICA FORMAL EBNF (ISO/IEC 14977)
Kernel: ZEPHYRUM 1.12 · Estado: IMPLEMENTADO (parser + bateria de prova)
Rótulo de maturidade: a sintaxe Dirac passa de ESPECIFICAÇÃO para
IMPLEMENTADO nesta versão, conforme critério da casa ("até o parser existir").

## 1. Programa

program = [ comment ] , ask_section , contract_section , model_section ,
          [ budget_section ] , [ require_section ] ;

## 2. Seções (ordem canônica fixa)

ask_section = "ASK:" , eol , indent , "question:" , predicate ;
contract_section = "CONTRACT:" , eol , indent , "absolute_error:" , number ;
model_section = "MODEL:" , eol , indent , "type:" , identifier ,
                { indent , model_entry } ;
budget_section = "BUDGET:" , eol , indent , budget_entry ,
                 { indent , budget_entry } ;
require_section = "REQUIRE:" , eol , indent , identifier ,
                  { indent , identifier } ;

model_entry = model_key , ":" , model_value ;
model_key = "state" | "terms" | "assumption" | identifier ;
model_value = number | number_list | dirac | identifier ;
budget_entry = "minimize" , ":" , identifier | identifier , ":" , identifier ;

## 3. Expressões e predicados

predicate = arith_expr , comparator , arith_expr ;
arith_expr = arith_term , { ( "+" | "-" ) , arith_term } ;
arith_term = arith_atom ;
arith_atom = number | identifier ;
comparator = "==" | "!=" | "<=" | ">=" | "<" | ">" ;

## 4. Literais Dirac

dirac = ket | bra ;
ket = "|" , dirac_body , ">" ;
bra = "<" , dirac_body , "|" ;
dirac_body = dirac_sym , { dirac_sym } ;
dirac_sym = identifier | number | "_" ;

## 5. Lexemas

number = [ "-" ] , digit , { digit } , [ "." , digit , { digit } ] ;
number_list = number , { "," , number } ;
identifier = letter , { letter | digit | "_" } ;
letter = "a" | "b" | … | "z" ;
digit = "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9" ;
comment = "#" , { any_char } , eol ;
indent = 1*{ " " } , (* entrada obrigatoriamente indentada dentro de seção *) ;
eol = "\n" ;

## 6. Semântica do parser (casa 1/0/REFUSED)

1. Entrada sintaticamente válida → status OK, AST canônica emitida.
2. Qualquer violação → REFUSED com linha e coluna exatas.
   O parser NUNCA adivina, NUNCA corrige silenciosamente:
   sintaxe ambígua é RECUSADA, não interpretada.

## 7. Regras canônicas verificadas pela bateria

R1. ASK precede CONTRACT, que precede MODEL; BUDGET e REQUIRE opcionais ao fim.
R2. ASK, CONTRACT e MODEL são obrigatórios.
R3. Chaves duplicadas na mesma seção → REFUSED.
R4. "type:" é obrigatório em MODEL e único.
R5. absolute_error é número (0 = erro absoluto zero: resposta exata).
R6. Lista com vírgula pendente ou vazia → REFUSED.
R7. Round-trip: AST → serialização canônica → re-parse → AST idêntica.
