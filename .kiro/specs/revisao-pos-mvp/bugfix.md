# Bugfix — revisão pós-implementação da Plataforma MVP

> Status: rascunho para aprovação  
> Responsável: Bruno  
> Atualizado em: 2026-07-31  
> Origem: revisão independente pós-implementação da spec `plataforma-mvp`

## Problema

A implementação da Plataforma MVP compila e a suíte automatizada atual passa, mas a revisão
independente encontrou falhas não cobertas pelos testes em segurança, integridade transacional,
privacidade, integração frontend/API, acessibilidade e governança de homologação.

Os problemas mais graves permitem alteração administrativa sem autorização regional, coleta de
dados fora da allowlist, moderação parcialmente persistida com resposta 500 e ausência de RLS nas
novas tabelas. Analytics e relatos também usam URLs que não são encaminhadas pelas aplicações
Next.js, tornando os fluxos inoperantes quando frontend e API são implantados separadamente.

A decisão registrada de `GO` não é sustentável enquanto esses defeitos e os portões de
homologação `0H` permanecerem abertos.

## Resultado esperado

- Tornar moderação e auditoria uma única operação atômica, sem persistência parcial.
- Restringir endpoints administrativos por papel, ação, objeto e escopo regional.
- Aplicar allowlist estrita aos eventos de analytics e rejeitar PII, coordenadas e texto livre.
- Adicionar throttling, RLS e retenção verificável aos módulos de analytics e relatos.
- Encaminhar corretamente todas as chamadas entre web, admin e API, com CSRF nas mutações.
- Vincular relatos a registros reais e preservar imutável o conteúdo originalmente enviado.
- Conectar operações editoriais ao workflow persistente, versionado e auditado.
- Permitir revogação imediata do consentimento opcional.
- Corrigir foco, teclado, semântica de diálogos e abas conforme WCAG 2.2 AA.
- Respeitar `prefers-color-scheme` quando não houver escolha persistida.
- Tornar falhas de autenticação e infraestrutura visíveis, sem convertê-las em estados vazios.
- Impedir que comandos de seed publiquem ou rebaixem conteúdo fora do workflow aprovado.
- Alinhar contratos OpenAPI às respostas reais e adicionar testes de integração negativos.
- Substituir a decisão de `GO` por `NO-GO` até a conclusão verificada desta spec e dos portões `0H`.

## Critérios de aceite

1. QUANDO uma moderação falhar em qualquer etapa O SISTEMA NÃO DEVE persistir mudança parcial.
2. QUANDO um usuário sem ação ou escopo regional autorizado acessar endpoints administrativos O
   SISTEMA DEVE responder `403` sem revelar conteúdo operacional ou contato do relator.
3. QUANDO um evento contiver propriedade não permitida, PII, coordenada ou texto livre O SISTEMA
   DEVE rejeitar integralmente o lote com resposta segura.
4. QUANDO o limite público de analytics ou relatos for excedido O SISTEMA DEVE responder `429`.
5. QUANDO as migrations forem aplicadas O SISTEMA DEVE comprovar RLS habilitado nas tabelas novas.
6. QUANDO frontend e API forem executados como serviços separados TODAS as chamadas previstas
   DEVEM alcançar a API correta, preservando cookies, CSRF e códigos de erro.
7. QUANDO o visitante revogar consentimento O SISTEMA DEVE interromper imediatamente novos eventos
   opcionais e limpar a fila local dessa finalidade.
8. QUANDO um relato for criado O SISTEMA DEVE validar a existência e coerência regional do alvo.
9. QUANDO um relato for moderado O SISTEMA NÃO DEVE permitir alteração do conteúdo original,
   contato ou identidade do alvo.
10. QUANDO um diálogo abrir O SISTEMA DEVE mover e conter o foco, fechar por `Escape` quando
    aplicável e restaurar o foco ao acionador.
11. QUANDO não houver tema salvo O SISTEMA DEVE respeitar `prefers-color-scheme`.
12. QUANDO ocorrer `401`, `403` ou erro de infraestrutura O PAINEL DEVE apresentar estado de erro
    correspondente, sem afirmar que não existem registros.
13. QUANDO o seed for executado O SISTEMA NÃO DEVE publicar, despublicar ou zerar versões fora do
    workflow editorial e da confirmação humana auditada.
14. QUANDO a verificação integrada terminar contratos, testes, lint, tipos e builds DEVEM passar,
    incluindo testes novos que falhavam antes das correções.
15. ENQUANTO qualquer bloqueador desta spec ou portão `0H` estiver aberto A DECISÃO DEVE permanecer
    `NO-GO` para homologação pública.

## Casos de borda e falhas obrigatórios

- Falha de auditoria depois da validação, mas antes do commit.
- Usuário autenticado sem grupo; papel correto sem escopo; escopo de região diferente.
- Payload aninhado, chave desconhecida, e-mail/telefone em valor e coordenada disfarçada.
- Duas ingestões concorrentes no mesmo agregado diário.
- Relato com UUID inexistente, slug divergente e região incompatível.
- Repetição de PATCH após timeout ou erro 500.
- Revogação com eventos ainda na fila local e requisição em andamento.
- API separada, indisponível, sessão expirada ou CSRF inválido.
- Navegação por teclado com `Tab`, `Shift+Tab`, `Escape`, setas, `Home` e `End`.
- Sistema em tema escuro sem preferência local e preferência salva divergente do sistema.
- Seed repetido sobre conteúdo já publicado e versionado.

## Fora do escopo

- Novas funcionalidades de produto não relacionadas aos achados.
- Ativação de Google Places, contratação de provedores ou abertura de tráfego público.
- Reformulação visual ampla além das correções de acessibilidade e estados de erro.
- Mudança da arquitetura Next.js + Django definida na spec principal.

_Requisitos afetados: RF-01, RF-07, RF-08, RF-10, RF-11, RF-12, RNF-01, RNF-02,
RNF-03, RNF-04, RNF-05, RNF-06, RNF-07, RNF-08, RB-01, RB-02, RB-06_
