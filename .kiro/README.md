# Sistema de desenvolvimento ECOnexão

Este diretório implementa um fluxo portátil inspirado em Kiro Specs:

```text
.kiro/
├── steering/                 # contexto permanente do produto
├── templates/                # modelos para novas specs
└── specs/
    ├── plataforma-mvp/       # fundação do produto
    ├── refinamento-visual-mobile/
    ├── adequacao-visual-proposta-mobile/
    └── documentacao-repositorio/
        ├── requirements.md
        ├── design.md
        └── tasks.md
```

## Como trabalhar

1. Comece em `requirements.md` e aprove o comportamento esperado.
2. Revise `design.md` e aprove as decisões técnicas.
3. Revise `tasks.md`, dependências e ordem de execução.
4. Peça ao Codex para “executar a tarefa X da spec plataforma-mvp”.
5. No Antigravity, use `/executar-spec plataforma-mvp`.

Os documentos antigos em `spec/` continuam sendo referências detalhadas. A pasta `.kiro/specs/` contém as unidades executáveis de desenvolvimento.

O catálogo de guias, materiais institucionais e evidências está em
[`docs/README.md`](../docs/README.md). Em caso de divergência, a direção e as specs
executáveis prevalecem sobre guias, apresentações e rascunhos.

## Specs visuais

- `refinamento-visual-mobile`: primeira compactação e implantação do tema escuro;
  concluída.
- `adequacao-visual-proposta-mobile`: especificação detalhada do app shell público em
  tela cheia no desktop, da composição móvel, da proposta fotográfica, do detalhe
  imersivo e do mapa; aguarda aprovação antes da implementação.
