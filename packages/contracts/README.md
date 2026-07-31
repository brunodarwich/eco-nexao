# @econexao/contracts

Contrato público da API v1 e tipos TypeScript derivados. A API Django é a fonte
de verdade; os artefatos deste pacote não devem ser editados manualmente.

- `pnpm contracts:generate`: regenera OpenAPI e tipos.
- `pnpm contracts:check`: valida o contrato e falha se os artefatos estiverem
  desatualizados.
- Importe os tipos com `import type { paths, components } from
"@econexao/contracts/api"`.
