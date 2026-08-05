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
    ├── revisao-pos-mvp/       # estabilização técnica ativa
    ├── painel-operacional/
    ├── painel-acompanhamento/
    ├── carga-local-inventario-pindobal/
    └── documentacao-repositorio/
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

## Estado das specs

| Spec | Estado | Próximo marco |
| --- | --- | --- |
| `plataforma-mvp` | implementação principal concluída; portões `0H` abertos | homologação depende de governança, provedores e verificação integrada |
| `revisao-pos-mvp` | ativa, em estabilização | concluir WCAG/tema, integração real, regressão e nova decisão humana go/no-go |
| `adequacao-visual-proposta-mobile` | aprovada e parcialmente implementada | contrato editorial de mídia e fotografias continuam bloqueados por acervo/curadoria |
| `refinamento-visual-mobile` | concluída | manutenção pela spec sucessora |
| `painel-operacional` | parcialmente entregue; três contratos administrativos bloqueados | especificar criação transacional, prontidão auditável e analytics por ponto; manter inclusão via CSV e estados indisponíveis até lá |
| `painel-acompanhamento` | concluída | manutenção do parser e da interface local |
| `carga-local-inventario-pindobal` | concluída | operação conforme guia de Pindobal |
| `documentacao-repositorio` | concluída | manter índices e relatórios sincronizados com as specs ativas |

Em 2026-08-05, a prioridade técnica é `revisao-pos-mvp`. A decisão permanece `NO-GO` para
homologação pública enquanto suas verificações finais e os portões `0H` estiverem abertos.
