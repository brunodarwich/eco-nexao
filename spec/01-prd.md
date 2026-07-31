# PRD — ECOnexão

> **Versão:** 0.2  
> **Status:** aprovado para fundação técnica  
> **Responsável pelo produto:** Bruno, interino

## 1. Resumo do produto

A **ECOnexão** é uma plataforma digital multirregional para descobrir, preparar e percorrer rotas turísticas. Ela reúne, em uma experiência única, informações da rota, mapa, etapas, empresas, prestadores de serviço, comunidades, instituições e pontos de apoio.

O produto será validado primeiro no eixo **Santarém–Alter do Chão**, com a **Rota de Pindobal** como modelo e cinco rotas no primeiro portfólio. O código e o modelo de dados, porém, serão preparados desde o início para múltiplas regiões. As expansões planejadas seguintes são **Altamira** e **Belém**.

## 2. Visão

Ser a infraestrutura digital que conecta turistas à oferta real de cada destino, permitindo que regiões diferentes publiquem rotas confiáveis, mantenham seus catálogos atualizados e compreendam como os visitantes interagem com o território.

## 3. Problemas

### Turista

- Pesquisa informações em fontes fragmentadas.
- Não sabe quais informações são atuais.
- Tem dificuldade para combinar rota, transporte, alimentação, hospedagem e segurança.
- Descobre poucos negócios e experiências fora dos canais mais digitalizados.
- Pode perder informações importantes quando está sem conexão.

### Empresa, prestador ou comunidade

- Aparece fora do contexto da jornada do turista.
- Tem dificuldade para manter vários canais atualizados.
- Não sabe quantos contatos foram influenciados por uma rota ou campanha.
- Pode ficar invisível mesmo sendo essencial para uma experiência.

### Operação da ECOnexão e parceiros territoriais

- Precisam transformar inventários e pesquisas em conteúdo publicável.
- Precisam saber quem alterou, verificou e publicou cada informação.
- Precisam importar e revisar dados em volume.
- Precisam medir uso sem criar rastreamento excessivo ou incompatível com a LGPD.

## 4. Objetivos do MVP

1. Permitir que um turista descubra uma rota e compreenda sua proposta.
2. Permitir que o turista prepare e percorra a rota, inclusive com conteúdo essencial offline.
3. Contextualizar empresas e prestadores dentro de cada rota.
4. Gerar contatos mensuráveis com atores locais.
5. Permitir que a equipe edite, importe, revise e publique conteúdo sem alterar código.
6. Medir o comportamento de navegação por eventos pseudonimizados e finalidades explícitas.
7. Comprovar que uma nova região pode ser incorporada sem reconstruir o produto.

## 5. Não objetivos do MVP

- Ser uma agência de viagens completa.
- Processar reservas, pagamentos ou cancelamentos.
- Criar uma rede social.
- Manter comentários e avaliações públicas.
- Criar conta obrigatória para o turista.
- Rastrear continuamente a localização do visitante.
- Construir navegação curva a curva.
- Publicar Altamira ou Belém antes da validação do método inicial.
- Permitir que uma automação ou IA publique conteúdo sem revisão humana.

## 6. Públicos e permissões

### Visitante

- Acessa sem login.
- Seleciona região.
- Explora rotas e catálogo.
- Usa o mapa e, opcionalmente, sua localização.
- Define preferências locais.
- Altera escolhas de privacidade.
- Envia relato de informação incorreta.

### Editor

- Cria e corrige regiões, rotas, etapas e itens do catálogo.
- Envia CSV e corrige erros de importação.
- Não publica conteúdo sozinho.

### Revisor

- Compara alterações, confere fontes e aprova conteúdo.
- Devolve registros para correção.

### Publicador

- Publica, suspende e restaura versões.
- Confirma alertas críticos.

### Administrador

- Gerencia acessos, permissões, configurações, integrações e auditoria.

### Analista

- Visualiza dashboards e exportações agregadas.
- Não acessa conteúdo privado ou identificadores brutos sem autorização específica.

## 7. Proposta de valor

### Para o turista

Uma forma simples de descobrir, preparar e percorrer rotas turísticas com informação confiável e acesso rápido aos serviços de cada região.

### Para empresas e prestadores

Presença dentro da jornada real do visitante, contatos qualificados e indicadores de interação.

### Para comunidades

Visibilidade contextualizada, participação na construção da rota e preservação do consentimento, da narrativa e do benefício local.

### Para parceiros institucionais

Uma base estruturada e atualizável da oferta turística, acompanhada de métricas agregadas de interesse e uso.

## 8. Princípios do produto

1. **Multirregional por arquitetura:** região é uma entidade do sistema, não uma configuração fixa.
2. **Rota como unidade principal:** mapa e catálogo existem dentro do contexto da rota.
3. **Confiança visível:** fonte, responsável e atualização fazem parte do conteúdo.
4. **Acesso progressivo:** o uso público não exige conta.
5. **Privacidade por padrão:** analytics opcional não é ativado antes da escolha do visitante.
6. **Localização sob demanda:** a posição precisa permanece no aparelho no MVP.
7. **Humano publica:** CSV, bot e IA criam rascunhos ou solicitações, nunca publicação automática.
8. **Conteúdo patrocinado identificado:** negociação comercial não altera silenciosamente a curadoria.
9. **Offline seletivo:** somente o núcleo necessário para percorrer a rota é baixado.
10. **Acessibilidade:** mapa sempre possui alternativa textual.

## 9. Escopo funcional

### Essencial

- Seleção e identificação da região atual.
- Página inicial com rotas em destaque.
- Tela de rotas com cards, busca e filtros.
- Detalhamento de rota.
- Abas de visão geral, mapa e catálogo.
- Etapas, preparação, alertas e pontos de apoio.
- Detalhe de empresa ou prestador.
- Contatos externos rastreáveis como intenção.
- Perfil local e configurações.
- Preferências de analytics e privacidade.
- Conteúdo offline por rota.
- Relato de informação incorreta.
- Dashboard administrativo.
- CRUD editorial de regiões, rotas e catálogo.
- Importação CSV com validação e histórico.
- Fluxo rascunho → revisão → aprovação → publicação.
- API REST pública e administrativa.
- Coleta de eventos em lote e painel agregado.

### Importante

- Favoritos armazenados localmente.
- Compartilhamento por link e QR Code.
- Busca unificada.
- Filtros de mapa e catálogo.
- Detecção de atualização do pacote offline.
- Exportação agregada de métricas.
- Rollback de publicação.
- Descoberta editorial assistida por fonte externa, condicionada a termos, custo e revisão.

### Futuro

- Conta do turista e sincronização entre dispositivos.
- Aplicativos nativos.
- Conteúdo multilíngue.
- Marketplace e reservas.
- Cadastro e edição via WhatsApp.
- Assistente de IA para estruturar alterações.
- Portal próprio para empresas reivindicarem perfis.
- Licenciamento operacional para outros destinos.

## 10. Requisitos funcionais

| ID | Requisito | Prioridade |
|---|---|---|
| RF-001 | O sistema deve permitir selecionar e trocar a região ativa | Essencial |
| RF-002 | O sistema deve listar somente rotas publicadas da região selecionada | Essencial |
| RF-003 | Cada card deve abrir o detalhamento da rota correta | Essencial |
| RF-004 | A rota deve apresentar visão geral, mapa e catálogo em abas | Essencial |
| RF-005 | O mapa deve mostrar traçado, etapas, alertas e atores relacionados | Essencial |
| RF-006 | O catálogo deve filtrar empresas e prestadores ligados à rota | Essencial |
| RF-007 | O visitante deve conseguir abrir contato ou navegação externa | Essencial |
| RF-008 | O visitante deve conseguir usar mapa/lista sem conceder localização | Essencial |
| RF-009 | O perfil local deve funcionar sem conta e permanecer no dispositivo | Essencial |
| RF-010 | Analytics opcional deve respeitar a preferência atual do visitante | Essencial |
| RF-011 | O painel deve permitir criar, editar, revisar e publicar conteúdo | Essencial |
| RF-012 | O painel deve importar catálogo por CSV sem publicar automaticamente | Essencial |
| RF-013 | Toda ação administrativa crítica deve gerar auditoria | Essencial |
| RF-014 | A API deve tratar região como parâmetro ou relação obrigatória | Essencial |
| RF-015 | Eventos devem ser aceitos em lote e validados por allowlist | Essencial |
| RF-016 | O conteúdo essencial da rota deve poder ser salvo offline | Essencial |
| RF-017 | O visitante deve poder relatar uma informação incorreta | Importante |
| RF-018 | Uma publicação deve poder voltar à versão anterior | Importante |
| RF-019 | A arquitetura deve aceitar solicitações futuras originadas no WhatsApp | Futuro |
| RF-020 | Uma proposta gerada por IA deve exigir aprovação humana | Futuro |
| RF-021 | O painel pode descobrir candidatos externos sem persistir ou publicar o retorno automaticamente | Importante |

## 11. Regras de negócio

- Uma rota pertence a uma região.
- Um item do catálogo pode aparecer em mais de uma rota e ter mais de uma localização.
- Uma rota pública deve referenciar somente registros publicados.
- Dados importados entram como rascunho ou “em revisão”.
- Publicação é versionada e atômica.
- Arquivar não apaga histórico.
- Contatos pessoais não são públicos sem autorização registrada.
- Informação crítica vencida bloqueia publicação ou gera alerta administrativo.
- A região selecionada pode vir de link, preferência local ou escolha explícita; geolocalização não é obrigatória.
- Uma interação de contato representa intenção, não venda confirmada.
- O painel de analytics deve trabalhar prioritariamente com agregados.
- Altamira e Belém usam o mesmo modelo de região, rota e catálogo do MVP.
- Resultado de fonte externa é candidato de curadoria e não cria dependência no produto público.

## 12. Métricas de sucesso

### Métrica principal

**Conexões qualificadas por visitante ativo**, como clique em WhatsApp, ligação, site, “como chegar” ou reserva externa depois da interação com uma rota ou item do catálogo.

### Funil principal

`visita → região → card da rota → detalhe → aba/ação → contato`

### Indicadores

- visitantes e sessões consentidas;
- taxa de clique nos cards;
- taxa de abertura de mapa e catálogo;
- rotas iniciadas e concluídas;
- uso e sucesso do pacote offline;
- visualizações e contatos por ator;
- origem por campanha, parceiro ou QR Code;
- utilidade percebida;
- dados críticos dentro da validade;
- tempo de correção;
- tempo de importação e taxa de erro do CSV;
- número de alterações estruturais necessárias para adicionar uma nova região.

## 13. Requisitos não funcionais

### Desempenho

- Conteúdo principal da página deve ser renderizado antes do mapa.
- Mapa deve ser carregado sob demanda.
- APIs públicas de leitura devem usar cache, ETag e paginação.
- Processamento de CSV e agregações pesadas devem ocorrer fora da requisição.

### Acessibilidade

- Meta WCAG 2.2 AA.
- Navegação por teclado.
- Botões com rótulos acessíveis.
- Pins sem dependência exclusiva de cor.
- Alternativa em lista para o mapa.

### Segurança

- HTTPS obrigatório.
- MFA obrigatório para perfis com publicação ou administração.
- Controle por papéis e princípio do menor privilégio.
- Logs sem dados pessoais desnecessários.
- Backup e restauração testados.

### Confiabilidade

- Publicação atômica.
- Jobs idempotentes.
- Auditoria de alterações críticas.
- Monitoramento de erros e disponibilidade.

## 14. Premissas e dependências

- O inventário inicial será transformado no CSV padrão.
- Os responsáveis por conteúdo confirmarão fontes e direitos de uso.
- A identidade visual será definida antes do desenvolvimento final das telas.
- Haverá infraestrutura para PostgreSQL/PostGIS e armazenamento de mídia.
- Política de privacidade, política de cookies e canal do titular serão aprovados antes da produção.
- A base legal de cada tratamento será revisada por profissional qualificado.

## 15. Decisões pendentes

- Quais serão as rotas 2 a 5?
- Haverá piloto fechado antes do acesso público?
- Quais preferências farão parte do perfil local?
- Favoritos entram na primeira publicação?
- Qual provedor de tiles será contratado para homologação?
- Quais serviços hospedarão API, frontend e mídia/CDN na homologação?
- Qual pessoa jurídica será a controladora dos dados?
- Quem exercerá o papel de encarregado ou canal de privacidade?
- Qual será a política comercial dos parceiros?

## 16. Histórico

| Data | Decisão | Motivo |
|---|---|---|
| 27/07/2026 | Posicionar a ECOnexão como plataforma multirregional | Evitar limitar o produto ao Tapajós |
| 27/07/2026 | Santarém–Alter do Chão como primeiro território | Base disponível e capacidade de validação |
| 27/07/2026 | Altamira e Belém como próximas expansões | Direção informada pelo projeto |
| 27/07/2026 | Backend em Python com Django | Administração, regras, API e auditoria no mesmo domínio |
| 27/07/2026 | Perfil local sem login no MVP | Entregar configurações sem criar coleta desnecessária |
| 27/07/2026 | Analytics próprios com consentimento para comportamento | Medir uso com maior controle sobre dados |
| 27/07/2026 | Bruno como responsável interino de produto e privacidade | Permitir a fundação mantendo a formalização como portão de homologação |
| 27/07/2026 | Next.js App Router, monorepo `pnpm` e Python com `uv` | Padronizar a fundação e a execução local |
| 27/07/2026 | MapLibre GL JS com tiles configuráveis | Evitar acoplamento do domínio ao provedor de mapas |
| 27/07/2026 | Supabase/PostGIS em `sa-east-1` para desenvolvimento e piloto | Manter o banco geográfico próximo ao território inicial |
| 29/07/2026 | Google Places somente como descoberta editorial opcional | Evitar dependência pública, cópia indevida de conteúdo e publicação automática |
