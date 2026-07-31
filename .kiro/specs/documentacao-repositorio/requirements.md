# Requisitos — documentação e organização do repositório

## Objetivo

Tornar a documentação da ECOnexão encontrável, atual e sustentável sem alterar o
comportamento do produto.

## Requisitos funcionais

### RF-DOC-01 — ponto de entrada

**Como** pessoa desenvolvedora ou colaboradora, **quero** encontrar no README da
raiz o propósito, a estrutura, a inicialização e os próximos documentos, **para**
começar sem percorrer arquivos não relacionados.

- QUANDO alguém abrir o repositório, O SISTEMA DE DOCUMENTAÇÃO DEVE indicar a fonte
  de verdade e separar documentação de produto, desenvolvimento, operação e acervo.
- QUANDO alguém precisar executar o app, O README DEVE fornecer comandos válidos e
  apontar para um guia detalhado.

### RF-DOC-02 — taxonomia documental

- A pasta `docs/` DEVE possuir um índice com proprietários conceituais e finalidade
  de cada coleção.
- A documentação operacional DEVE distinguir entrada, artefato gerado e evidência.
- Materiais históricos ou institucionais NÃO DEVEM ser apresentados como fonte de
  verdade vigente.

### RF-DOC-03 — arquitetura e operação

- A documentação DEVE descrever os componentes existentes do monorepo e seus limites.
- A documentação DEVE registrar o fluxo local, URLs, validação e operações da rota
  demonstrativa sem expor segredos.

### RF-DOC-04 — manutenção

- Mudanças de comportamento ou arquitetura DEVEM continuar sendo feitas primeiro nas
  specs executáveis em `.kiro/specs/`.
- Links locais e formatação dos documentos alterados DEVEM ser verificados.

## Requisitos não funcionais

- **RNF-DOC-01:** texto em português brasileiro, conciso e navegável.
- **RNF-DOC-02:** nenhum segredo ou conteúdo de `.env` pode ser lido ou reproduzido.
- **RNF-DOC-03:** a reorganização não pode quebrar caminhos usados por scripts.
- **RNF-DOC-04:** exemplos devem funcionar em PowerShell a partir da raiz.

## Casos de borda

- O Supabase pode estar indisponível; os guias devem diferenciar instalação de ações
  que dependem de infraestrutura externa.
- Arquivos CSV e evidências visuais podem ser grandes; o índice deve descrevê-los sem
  incorporá-los ao README principal.
- Documentos históricos podem divergir das specs; a precedência deve ser explícita.
