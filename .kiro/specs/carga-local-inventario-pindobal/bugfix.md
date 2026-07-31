# Bugfix — carga local do inventário de Pindobal

## Problema

O adaptador gera 181 linhas canônicas, mas o fluxo termina em rascunhos privados e o banco
local contém somente dois atores demonstrativos. Assim, o app público não apresenta o
inventário que o responsável pelo produto autorizou publicar no ambiente local.

## Resultado esperado

- Carregar idempotentemente as 181 linhas canônicas no domínio de catálogo.
- Publicá-las somente mediante confirmação explícita na linha de comando.
- Criar localização pública apenas quando houver coordenadas válidas.
- Vincular os 181 atores à rota informada no CSV.
- Não carregar as 14 linhas Google mantidas no arquivo de quarentena.
- Despublicar os dois atores demonstrativos, preservando-os para recuperação e sem inflar a
  contagem pública.

_Requisitos: RF-04, RF-05, RF-08, RNF-03, RNF-08_
