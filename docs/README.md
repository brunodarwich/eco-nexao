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
| backup, rollback e resposta a incidentes     | [backup e incidentes](operations/incidents-and-rollback.md)          |
| consultar relatório de Go/No-Go do piloto    | [relatório de Go/No-Go](operations/pilot-go-no-go-report.md)          |
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

## Artefatos e Organização

- `assets/brand/`: logos preparados para uso pelo produto.
- `data/pindobal/`: entradas operacionais e inventário bruto em CSV.
- `docs/acervo/`: rascunhos de propostas (`proposals/`) e arquivos visuais originais (`visuals/`).
- `outputs/`: resultados reproduzíveis de ferramentas; não são documentação normativa.

## Manutenção

Uma mudança funcional começa em requirements, design e tasks da spec correspondente. Guias
devem explicar o estado implementado e conter apenas exemplos sem segredos. Ao adicionar uma
nova coleção, inclua-a neste índice e defina sua finalidade.
