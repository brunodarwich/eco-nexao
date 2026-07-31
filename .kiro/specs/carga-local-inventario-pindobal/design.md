# Design — carga local do inventário de Pindobal

Uma management command recebe o CSV canônico já validado, exige a opção explícita
`--confirm-publish-unverified` e executa toda a materialização em uma transação. Categorias,
atores, localizações e vínculos de rota usam chaves naturais e `update_or_create`, tornando a
operação repetível. Contatos permanecem privados porque o CSV declara
`public_contact_authorized=false`. Os fixtures demonstrativos são mantidos no banco como
rascunho e, por isso, deixam de aparecer na API pública.

O comando aceita apenas `source_type` institucional/inventário/campo/direto/web público,
rejeita fontes Google e mantém no texto público o aviso de revisão já presente no CSV. Atores
recebem status publicado por autorização humana explícita do responsável pelo produto neste
ambiente local. O comando não altera arquivos de quarentena nem referências externas.

Testes cobrem confirmação obrigatória, carga, ausência de pin sem coordenadas, exclusão dos
vínculos demonstrativos e idempotência.
