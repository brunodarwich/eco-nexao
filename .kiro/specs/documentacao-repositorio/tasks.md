# Tarefas — documentação e organização do repositório

- [x] DOC-1. Criar a taxonomia e o índice da documentação
  - _Requisitos: RF-DOC-01, RF-DOC-02, RNF-DOC-01_
- [x] DOC-2. Atualizar o ponto de entrada e os guias de arquitetura, desenvolvimento e operação
  - Depende de: DOC-1
  - _Requisitos: RF-DOC-01, RF-DOC-03, RNF-DOC-02, RNF-DOC-04_
  - Arquivos: `README.md`, `docs/README.md`, `docs/architecture/overview.md`,
    `docs/development/setup.md`, `docs/operations/pindobal.md`, `.kiro/README.md`
- [x] DOC-3. Verificar links, formatação, comandos e registrar evidências
  - Depende de: DOC-2
  - _Requisitos: RF-DOC-04, RNF-DOC-03_
  - Verificação: Prettier local nos nove Markdown alterados; verificador PowerShell de links
    relativos; busca por espaços finais; `git diff --check`; comandos confrontados com os
    scripts de `package.json` e `pyproject.toml`.
