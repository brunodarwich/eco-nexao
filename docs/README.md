# Documentação ECOnexão

Este diretório reúne guias de apoio, operação, materiais de apresentação e evidências.
Decisões de produto e implementação continuam nas specs.

## Onde encontrar cada informação

| Preciso de…                                  | Documento                                                             |
| -------------------------------------------- | --------------------------------------------------------------------- |
| visão geral e comandos essenciais            | [README do repositório](../README.md)                                 |
| instalar, executar ou validar localmente     | [desenvolvimento local](development/setup.md)                         |
| entender os componentes e limites do sistema | [visão de arquitetura](architecture/overview.md)                      |
| operar os dados demonstrativos de Pindobal   | [operação de Pindobal](operations/pindobal.md)                        |
| requisitos detalhados do produto             | [índice da especificação](../spec/README.md)                          |
| executar tarefas aprovadas                   | [sistema de specs](../.kiro/README.md)                                |
| consultar o contrato da API                  | [pacote de contratos](../packages/contracts/README.md)                |
| acompanhar tarefas localmente                | [painel de desenvolvimento](../tools/development_dashboard/README.md) |

## Coleções

- `apresentacoes/`: propostas e materiais institucionais; não são fonte normativa.
- `design-proposals/`: referências visuais e propostas de composição.
- `visual-evidence/`: capturas usadas como evidência de verificação visual.
- `architecture/`: explicações do sistema implementado.
- `development/`: ambiente e fluxo de contribuição.
- `operations/`: procedimentos repetíveis e seus limites de segurança.

## Fonte de verdade

A precedência é: `.kiro/steering/` → `.kiro/specs/` → `spec/` → guias em `docs/` →
READMEs locais. Rascunhos e apresentações preservam contexto histórico, mas não substituem
uma spec aprovada.

## Artefatos fora de `docs/`

- `assets/brand/`: logos preparados para uso pelo produto.
- CSVs na raiz: entradas operacionais mantidas nos caminhos usados pelos comandos atuais.
- `outputs/`: resultados reproduzíveis de ferramentas; não são documentação normativa.
- `01-topicos-principais.md`, `02-rascunho-proposta-econexao.md`, logos originais e
  `planejamento-visual-econexao.html`: acervo de origem preservado na raiz para evitar quebra
  de referências durante esta reorganização.

## Manutenção

Uma mudança funcional começa em requirements, design e tasks da spec correspondente. Guias
devem explicar o estado implementado e conter apenas exemplos sem segredos. Ao adicionar uma
nova coleção, inclua-a neste índice e defina sua finalidade.
