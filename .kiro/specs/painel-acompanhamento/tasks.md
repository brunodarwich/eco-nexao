# Tasks - Painel de acompanhamento do desenvolvimento

> Status: aprovado e em execução

## Implementação

- [x] DEV-1. Criar painel local de acompanhamento em Streamlit
  - Dependências: nenhuma
  - [x] DEV-1.1 Implementar parser somente leitura para os `tasks.md`
  - [x] DEV-1.2 Implementar recomendação de próxima etapa e filtros
  - [x] DEV-1.3 Criar visão executiva, Kanban e bloqueios com identidade ECOnexão
  - [x] DEV-1.4 Adicionar atualização automática e manual
  - [x] DEV-1.5 Criar testes e documentação de execução
  - _Requisitos: RF-DEV-01, RF-DEV-02, RF-DEV-03, RF-DEV-04, RNF-DEV-01, RNF-DEV-02, RNF-DEV-03_
  - Arquivos: `tools/development_dashboard/`, `package.json`
  - Verificação: `ruff check`, `ruff format --check`, `pytest` e smoke test Streamlit

## Verificação

- [x] DEV-V1. Executar testes do parser e do motor de recomendação
  - Dependências: DEV-1
  - _Requisitos: RNF-DEV-03_
  - Verificação: 6 testes aprovados em 2026-07-27
- [x] DEV-V2. Validar o painel no navegador em tema claro e responsivo
  - Dependências: DEV-1
  - _Requisitos: RNF-DEV-01_
  - Verificação: visão geral e Kanban validados em desktop e viewport móvel 390x844
