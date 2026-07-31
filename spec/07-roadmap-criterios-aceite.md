# Roadmap, prioridades e critérios de aceite

> O cronograma deve ser convertido em datas somente depois de confirmar equipe, dedicação, infraestrutura e estado real do conteúdo. As fases abaixo representam dependências, não estimativas comerciais.

## 1. Prioridades

### P0 — bloqueia o piloto

- Região multirregional no modelo de dados.
- PWA com início, rotas e detalhamento.
- Abas visão geral, mapa e catálogo.
- Perfil local e configurações.
- Backend Django e APIs públicas.
- Painel administrativo e papéis.
- Importação CSV com prévia.
- Publicação versionada.
- Analytics com consentimento.
- Política, canal do titular e controles LGPD.
- Testes de segurança, offline e acessibilidade.

### P1 — fortalece a validação

- Favoritos.
- Compartilhamento e QR Codes.
- Relatos offline.
- Dashboard avançado.
- Exportação agregada.
- Rollback completo de importações.
- Filtros avançados.
- Automação de verificação de dados vencidos.
- Descoberta editorial opcional por Google Places, após cumprir os portões do provedor.

### P2 — depois do piloto

- Altamira e Belém.
- Conta de turista.
- Multilíngue.
- Aplicativos nativos.
- Portal de parceiros.
- WhatsApp e IA.
- Reservas e pagamentos.

## 2. Fases

### Fase 0 — decisões e preparação

### Entregáveis

- PRD aprovado.
- Rotas 1 a 5 definidas.
- Proprietários de produto, conteúdo, tecnologia e privacidade.
- Controlador e canal LGPD definidos.
- Identidade e promessa aprovadas.
- Provedor de mapa e infraestrutura escolhidos.
- Inventário convertido para o CSV padrão.

### Portão

Não iniciar desenvolvimento amplo sem confirmar a rota-modelo, os dados disponíveis e quem pode aprovar conteúdo.

### Fase 1 — fundação técnica

### Backend

- Projeto Django.
- PostgreSQL/PostGIS.
- Módulos `accounts`, `regions`, `routes`, `catalog` e `audit`.
- OpenAPI.
- Ambientes.
- CI.

### Frontend

- Estrutura PWA.
- Design tokens.
- Navegação.
- Tela inicial vazia conectada à API.
- Estados comuns.

### Aceite

- Região é carregada pelo banco.
- PWA e API são implantadas em homologação.
- Usuário administrativo entra com MFA.
- OpenAPI é validado no CI.

### Fase 2 — corte vertical de Pindobal

### Entregáveis

- Região Santarém–Alter do Chão.
- Rota de Pindobal.
- Visão geral.
- Etapas.
- Mapa e lista.
- Catálogo contextual.
- Detalhe de ator.
- Contatos externos.
- Editor administrativo básico.

### Aceite

- Turista percorre o fluxo card → rota → mapa/catálogo → contato.
- Conteúdo vem da API publicada.
- Coordenadas inválidas são rejeitadas.
- Nenhum rascunho aparece publicamente.

### Fase 3 — operação editorial e CSV

### Entregáveis

- Fontes e verificações.
- Estados editoriais.
- Importação CSV.
- Prévia e erros.
- Revisão.
- Publicação atômica.
- Histórico e rollback.
- Prévia de candidatos externos autenticada, atribuída e efêmera.

### Aceite

- Arquivo template válido importa como rascunho.
- Arquivo inválido informa linha e coluna.
- Reimportação não duplica.
- Publicação gera snapshot e auditoria.
- Versão anterior permanece se o job falhar.
- Falha ou cota do provedor externo não impede cadastro e revisão manuais.
- Nenhum payload do Google Places é persistido ou exibido no MapLibre.

### Fase 4 — perfil, offline e relatos

### Entregáveis

- Perfil local.
- Região preferida.
- Preferências.
- Favoritos, se confirmado.
- Download offline.
- Atualização de pacote.
- Relato com outbox.

### Aceite

- Perfil funciona sem login.
- Limpar dados remove preferências locais.
- Rota salva abre sem rede.
- Pacote corrompido não substitui versão válida.
- Relato em fila é sincronizado uma vez.

### Fase 5 — analytics e LGPD

### Entregáveis

- Banner e central de privacidade.
- SDK interno.
- API em lote.
- Allowlist.
- Agregações.
- Funil no dashboard.
- Retenção automatizada.
- Canal de direitos.
- Documentos jurídicos aprovados.

### Aceite

- Aceitar, recusar e revogar funcionam.
- Não há evento opcional antes da escolha.
- Coordenadas e texto livre são rejeitados.
- Eventos duplicados não aumentam métricas.
- Dashboard mostra o funil agregado.
- Expiração é testada.

### Fase 6 — cinco rotas e piloto

### Entregáveis

- Rotas 2 a 5.
- Critérios de prontidão por rota.
- QR Codes e canais.
- Teste de campo.
- Monitoramento.
- Suporte ao piloto.

### Aceite

- Cinco rotas publicadas no mesmo padrão.
- Cada rota passa por validação editorial, geográfica, offline e de direitos.
- Métricas podem ser separadas por rota.
- Nenhuma rota exige mudança estrutural improvisada.

### Fase 7 — expansão multirregional

### Entregáveis

- Primeira região seguinte, recomendada após decisão entre Altamira e Belém.
- Novo catálogo.
- Novas rotas.
- Adaptação editorial.
- Teste de região.

### Aceite

- Região é adicionada por dados e configuração.
- APIs, URLs, filtros e dashboard separam regiões.
- O código não contém regra fixa para Tapajós.
- A região inicial continua funcionando sem regressão.

### Fase 8 — WhatsApp e IA

### Pré-condições

- Processo editorial maduro.
- Responsáveis e SLA definidos.
- Provedor contratado.
- Avaliação LGPD específica.
- Política de retenção de conversas.
- Limites da IA aprovados.

### Entregáveis

- Webhook assinado.
- Deduplicação.
- Consentimento/aviso no canal.
- Extração estruturada.
- Fila de alteração.
- Diff.
- Revisão humana.
- Retorno ao solicitante.

### Aceite

- Mensagem repetida não cria solicitação duplicada.
- Telefone não aparece no conteúdo público por padrão.
- IA não publica.
- Revisor enxerga fonte, proposta e confiança.
- Aprovação gera auditoria.

## 3. Critérios por épico

### Épico A — regiões

- Criar, editar e arquivar região.
- Selecionar região no público.
- Filtrar rotas e catálogo.
- URL preserva contexto.
- Região não publicada não aparece na API pública.

### Épico B — rotas

- Card abre rota correta.
- Três abas possuem URL.
- Preparação e etapas são legíveis.
- Alertas ativos aparecem.
- Fonte e atualização são exibidas.
- Rota suspensa não pode ser iniciada.

### Épico C — mapa

- Traçado e pins carregam.
- Lista alternativa funciona.
- Localização só é pedida por ação.
- Negar permissão não bloqueia.
- Coordenada fica local.
- Mapa falho não remove acesso ao conteúdo.

### Épico D — catálogo

- Item pode pertencer a múltiplas rotas.
- Filtros funcionam.
- Contato autorizado aparece.
- Contato não autorizado fica privado.
- Patrocínio é rotulado.
- Cliques são medidos sem registrar o destino pessoal.

### Épico E — perfil

- Não exige conta.
- Preferências persistem localmente.
- Acessibilidade não é enviada em analytics.
- Região preferida é alterável.
- Limpeza local é confirmada e efetiva.

### Épico F — painel

- Papéis limitam ações.
- Rascunho e publicado são distintos.
- Revisor compara mudanças.
- Publicação exige permissão.
- Rollback funciona.
- Auditoria registra ação crítica.

### Épico G — CSV

- Template é aceito.
- Validações bloqueantes e avisos são separados.
- Prévia ocorre antes de commit.
- Commit cria rascunhos.
- `external_id` mantém idempotência.
- Arquivo e erro ficam restritos.

### Épico H — analytics

- Eventos possuem schema.
- Consentimento é respeitado.
- Allowlist existe no cliente e servidor.
- Funis podem ser reproduzidos.
- Retenção é aplicada.
- Dashboard não expõe perfil individual.

### Épico I — descoberta editorial externa

- Chave permanece exclusivamente no backend.
- Busca exige papel administrativo e parâmetros limitados.
- Resultado aparece como prévia efêmera atribuída ao `Google Maps`.
- Place ID usa referência de fonte própria; não substitui `external_id`.
- Conteúdo externo não entra em cache, pacote offline, MapLibre ou API pública.
- Custo, cota, erro e indisponibilidade possuem limites e modo degradado.

## 4. Estratégia de testes

### Unitários

- Regras de prontidão.
- Permissões.
- Importação.
- Idempotência.
- Validação de eventos.
- Publicação.
- Retenção.

### Integração

- API + banco.
- PostGIS.
- Job + fila.
- Snapshot + storage.
- Consentimento + ingestão.
- Webhook futuro + change request.
- Google Places com transporte falso, sem rede nem persistência.

### E2E

- Selecionar região.
- Abrir card e navegar pelas abas.
- Usar mapa sem localização.
- Abrir contato.
- Alterar privacidade.
- Importar CSV.
- Revisar e publicar.
- Restaurar versão.

### Acessibilidade

- Teclado.
- Leitor de tela.
- Contraste.
- Foco.
- Alternativa textual do mapa.
- Zoom de texto.

### Segurança

- Autorização.
- CSRF e CORS.
- Upload malicioso.
- Rate limit.
- Vazamento em logs.
- Escalada de papel.
- Assinatura de webhook.

### Privacidade

- Primeira visita sem decisão.
- Recusa.
- Aceite.
- Revogação.
- Limpeza local.
- Propriedade proibida.
- Pedido de acesso/exclusão.
- Expiração.

### Desempenho

- Catálogo grande.
- Mapa com muitos pins.
- CSV com limite máximo.
- Lote de eventos.
- Conteúdo offline.
- Rede 3G/4G instável.

## 5. Definição de pronto

Uma funcionalidade só está pronta quando:

- requisito e design foram aprovados;
- critérios de aceite passam;
- testes automatizados proporcionais existem;
- acessibilidade foi verificada;
- eventos foram validados ou explicitamente dispensados;
- impacto de privacidade foi avaliado;
- logs e métricas operacionais existem;
- documentação e OpenAPI foram atualizados;
- erro e estado vazio foram implementados;
- não existem dados fictícios apresentados como reais.

## 6. Go-live do piloto

### Produto

- Pindobal pronta.
- Fluxos P0 passam.
- Offline testado em campo.
- Links e QR Codes testados.

### Conteúdo

- Fontes registradas.
- Dados críticos válidos.
- Direitos de mídia e contatos confirmados.
- Alertas e contatos de emergência revisados.

### Tecnologia

- Backup e restauração testados.
- Monitoramento ativo.
- Rollback ensaiado.
- Limites e alertas configurados.

### Privacidade

- Controlador e canal publicados.
- Avisos aprovados.
- Consentimento testado.
- Retenção automatizada.
- Operadores registrados.
- Plano de incidente disponível.

### Operação

- Escala de responsáveis.
- SLA de relatos.
- Procedimento de suspensão.
- Treinamento do painel.
- Plano de suporte.

## 7. Riscos de cronograma

| Risco | Impacto | Resposta |
|---|---|---|
| Cinco rotas sem dados prontos | produto raso | Pindobal vertical primeiro |
| Importação com baixa qualidade | retrabalho | dry-run, avisos e revisão |
| Mapa/offline complexos | atraso | lista como fallback e pacote mínimo |
| Analytics implementado tarde | falta de aprendizagem | schema e consentimento desde a fundação |
| LGPD tratada só no fim | bloqueio de lançamento | inventário e revisão durante desenvolvimento |
| WhatsApp antecipado | aumento de escopo | manter apenas contratos e pontos de extensão |
| Data fixa sem capacidade | corte de qualidade | replanejar pelo portão de prontidão |
