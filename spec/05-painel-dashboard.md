# Dashboard e painel administrativo

## 1. Distinção

- **Dashboard:** visão resumida do estado do produto, conteúdo, importações, uso e pendências.
- **Painel administrativo:** ambiente operacional para cadastrar, editar, revisar, publicar, importar e auditar.

Ambos exigem autenticação. O dashboard é a página inicial do painel.

## 2. Navegação administrativa

```text
/admin
├── /dashboard
├── /regions
├── /routes
│   └── /{routeId}
│       ├── /content
│       ├── /stages
│       ├── /map
│       ├── /catalog
│       ├── /alerts
│       ├── /sources
│       ├── /preview
│       └── /history
├── /catalog
│   ├── /discovery
│   └── /{actorId}
├── /imports
│   └── /{importId}
├── /reports
├── /change-requests
├── /analytics
├── /privacy
├── /audit
├── /users
└── /settings
```

## 3. Dashboard inicial

### Objetivo

Mostrar o que precisa de atenção e permitir que a equipe retome rapidamente o trabalho.

### Indicadores de conteúdo

- Regiões cadastradas, em preparação e publicadas.
- Rotas por estado editorial.
- Percentual de prontidão por rota.
- Dados críticos vencidos.
- Alertas ativos.
- Itens do catálogo por região e categoria.
- Registros sem fonte ou autorização.
- Pacotes offline pendentes ou com falha.

### Indicadores operacionais

- Importações em andamento ou com erro.
- Relatos aguardando triagem.
- Solicitações de alteração.
- Publicações recentes.
- Jobs com falha.
- Incidentes e alertas internos.

### Indicadores de uso

- Visitantes e sessões consentidas.
- Rotas mais abertas.
- Taxa de abertura de mapa e catálogo.
- Conexões qualificadas.
- Contatos por ator e categoria.
- Origem por campanha, parceiro ou QR Code.
- Sucesso de download e abertura offline.

### Filtros

- Período.
- Região.
- Rota.
- Canal de aquisição.
- Dispositivo.
- Tipo de conexão.

Não deve existir filtro para seguir uma pessoa individual.

## 4. Placar de prontidão das rotas

Cada rota recebe dimensões separadas:

| Dimensão | Exemplos de bloqueio |
|---|---|
| Conteúdo | descrição, preparação ou etapa ausente |
| Geografia | traçado inválido ou ponto fora do limite |
| Catálogo | ausência de apoios mínimos |
| Segurança | alerta crítico não revisado |
| Fontes | dado crítico sem fonte ou validade |
| Direitos | imagem ou contato sem autorização |
| Offline | pacote não gerado ou checksum inválido |
| Qualidade | testes ou preview pendentes |

Estados:

- vermelho: bloqueia publicação;
- amarelo: aviso que exige decisão;
- verde: pronto;
- cinza: não aplicável.

O percentual geral nunca pode esconder bloqueio crítico.

## 5. Editor de região

### Campos

- nome público;
- slug;
- resumo;
- imagem;
- centro do mapa;
- limite operacional;
- fuso horário;
- estado editorial;
- ordem de exibição;
- SEO;
- contatos institucionais privados;
- fontes.

### Botões

- `Salvar rascunho`.
- `Enviar para revisão`.
- `Pré-visualizar`.
- `Arquivar`.

Altamira e Belém poderão ser cadastradas como regiões em preparação sem serem exibidas publicamente.

## 6. Editor de rota

### Seções

1. Identidade.
2. Preparação.
3. Etapas.
4. Traçado.
5. Catálogo e pontos de apoio.
6. Alertas.
7. Mídia.
8. Fontes e verificações.
9. Offline.
10. SEO e compartilhamento.
11. Histórico.

### Botões

| Botão | Permissão | Resultado |
|---|---|---|
| `Salvar rascunho` | Editor | grava sem publicar |
| `Duplicar estrutura` | Editor | cria nova rota sem copiar confirmações |
| `Validar` | Editor/Revisor | executa regras |
| `Enviar para revisão` | Editor | bloqueia edição concorrente ou cria revisão |
| `Aprovar` | Revisor | torna elegível para publicação |
| `Devolver` | Revisor | exige motivo |
| `Publicar` | Publicador | cria versão atômica |
| `Suspender` | Publicador | remove versão da exposição |
| `Restaurar versão` | Publicador | aponta para versão anterior |

### Regras

- Duplicar rota não duplica validação, direitos ou datas como se fossem atuais.
- Alteração posterior à aprovação exige nova revisão.
- Publicador visualiza o diff final.
- Alertas críticos podem suspender uma rota sem apagar conteúdo.

## 7. Editor do catálogo

### Busca e filtros

- Região.
- Rota.
- Categoria.
- Estado editorial.
- Verificação.
- Autorização de contato.
- Parceria.
- Importação de origem.
- Possível duplicidade.

### Abas do registro

- Identidade.
- Localizações.
- Categorias e serviços.
- Contatos.
- Horários.
- Rotas relacionadas.
- Mídia.
- Fontes e verificações.
- Parceria.
- Histórico.

### Ações em lote

- Vincular categoria.
- Vincular rota.
- Enviar para revisão.
- Arquivar.
- Solicitar confirmação.

Publicação em lote exige resumo dos impactos e confirmação reforçada.

### Descoberta de candidatos externos

A rota `/admin/catalog/discovery` permite que editor, revisor ou administrador consulte
fontes externas sem misturar os resultados com o catálogo persistido.

Para Google Places, a tela:

- exige região, rota ou centro, raio, tipos e limite;
- mostra prévia efêmera em um contêiner visual separado;
- exibe atribuição oficial `Google Maps` próxima aos resultados;
- informa que o ranking considera relevância, distância e destaque;
- oferece link para abrir o resultado original;
- não oferece exportação, cache, exibição no MapLibre ou publicação direta;
- permite iniciar um rascunho vazio, que deverá ser preenchido com dados verificados em fonte
  autorizada;
- encerra com estado recuperável quando a integração está ausente, sem cota ou indisponível.

A ativação depende de autenticação, autorização, termos, privacidade, orçamento, cotas e chave
restrita. Fotografias, avaliações e resumos de IA do provedor ficam fora do primeiro corte.

## 8. Importação CSV

### Etapa 1 — envio

Elementos:

- seletor de arquivo;
- link para baixar template;
- região padrão opcional;
- modo estrito;
- explicação sobre dados proibidos.

Botão: `Enviar e validar`.

### Etapa 2 — prévia

Mostrar:

- arquivo, hash, autor e data;
- total de linhas;
- novas, atualizadas, arquivadas;
- avisos e erros;
- possíveis duplicidades;
- amostra antes/depois.

Botões:

- `Baixar erros`.
- `Corrigir mapeamento`.
- `Cancelar importação`.
- `Confirmar como rascunho`.

### Etapa 3 — processamento

- Barra de progresso.
- Contadores.
- Job e correlação.
- Possibilidade de sair da tela.

### Etapa 4 — resultado

- Resumo final.
- Registros criados/alterados.
- Linhas rejeitadas.
- Link para filtrar registros daquele lote.
- Botão `Reverter lote`, quando tecnicamente seguro.
- Botão `Iniciar revisão`.

### Regras

- O botão de confirmar nunca diz apenas “Importar”; deve explicitar “como rascunho”.
- Importação não publica.
- Linha inválida não deve corromper linhas válidas.
- Modo atômico completo pode ser oferecido como configuração administrativa.
- O arquivo original não fica publicamente acessível.

## 9. Central de relatos

### Fila

- Novo.
- Em triagem.
- Em verificação.
- Resolvido.
- Rejeitado.
- Duplicado.

### Priorização

1. Segurança e saúde.
2. Acesso e transporte.
3. Horário e contato.
4. Conteúdo editorial.
5. Sugestões gerais.

### Ações

- Atribuir responsável.
- Vincular a uma entidade.
- Criar proposta de alteração.
- Pedir complemento.
- Resolver.
- Suspender informação.

Texto e contato do relato possuem acesso mais restrito do que seu estado operacional.

## 10. Solicitações de alteração

Essa fila recebe:

- mudanças manuais;
- resultados de importação;
- relatos convertidos;
- futuro WhatsApp;
- futuras propostas de IA.

### Tela de comparação

- Valor publicado.
- Valor atual do rascunho.
- Valor proposto.
- Fonte.
- Solicitante e canal.
- Confiança da IA, se houver.
- Histórico.
- Riscos.

### Botões

- `Aceitar campo`.
- `Rejeitar campo`.
- `Aceitar todos os campos válidos`.
- `Pedir informação`.
- `Salvar como rascunho`.
- `Enviar para revisão`.

Não existe botão “Publicar resposta da IA”.

## 11. Analytics administrativo

### Visões

1. **Visão geral**
2. **Funil**
3. **Rotas**
4. **Mapa e etapas**
5. **Catálogo e contatos**
6. **Campanhas e QR Codes**
7. **Offline**
8. **Qualidade técnica**

### Funil configurado

`home → card → detalhe → aba → ator → contato`

### Relatórios

- Visualizações e CTR por posição do card.
- Taxa de abertura de cada aba.
- Pins e categorias mais acionados.
- Abandono entre preparação e início.
- Contatos por rota e ator.
- Sucesso de offline.
- Erros por versão.

### Salvaguardas

- Resultados com grupos muito pequenos podem ser suprimidos.
- Identificadores brutos não aparecem na interface padrão.
- Exportações têm permissão, finalidade, marca d'água ou auditoria.
- Não há replay de sessão no MVP.
- Não há mapa de trajetória individual.

## 12. Central de privacidade administrativa

### Funções

- Acompanhar solicitações de titulares.
- Consultar versão de consentimento.
- Executar exportação ou eliminação controlada.
- Registrar fundamento, responsável e prazo.
- Revisar retenção.
- Registrar incidentes.

### Estados do pedido

- Recebido.
- Identidade/prova em validação.
- Em atendimento.
- Concluído.
- Parcialmente atendido com justificativa.
- Rejeitado com fundamento.

## 13. Auditoria

Registrar:

- login e mudança de MFA;
- criação e remoção de acesso;
- importação e rollback;
- alteração de contato público;
- aprovação e publicação;
- suspensão e restauração;
- exportação de dados;
- atendimento de direito do titular;
- mudança de retenção ou consentimento;
- ação de integração/IA.

Campos:

- ator administrativo;
- ação;
- entidade;
- antes/depois minimizado;
- data;
- IP de segurança com retenção separada;
- `request_id`;
- motivo;
- resultado.

## 14. Estados e erros do painel

- Sessão expirada: preservar rascunho local quando seguro.
- Conflito de edição: mostrar versão atual e opções de recarregar/comparar.
- Falha de validação: indicar seção e campo.
- Falha de job: permitir repetir de forma idempotente.
- Sem permissão: explicar que a ação requer outro papel.
- Publicação concorrente: bloquear e exibir operação ativa.
- Serviço externo indisponível: manter rascunho e não publicar parcialmente.

## 15. Critérios de aceite

- Dashboard abre com filtros de região e período.
- Usuário vê somente funções compatíveis com seu papel.
- Editor consegue montar rota e relacionar itens do catálogo.
- Revisor enxerga fontes, verificações e diff.
- Publicador consegue publicar e restaurar versão anterior.
- CSV possui validação e prévia antes da confirmação.
- Importação confirmada cria rascunhos.
- Dashboard de analytics exibe agregados sem consulta por indivíduo.
- Toda ação crítica aparece na auditoria.
- Solicitação futura de WhatsApp/IA entra na mesma fila de revisão.
- Descoberta externa é autenticada, atribuída, efêmera e nunca publica ou preenche um registro automaticamente.
