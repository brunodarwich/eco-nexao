# Requirements - Plataforma MVP ECOnexão

> Status: aprovado para fundação técnica  
> Responsável pelo produto: Bruno, interino  
> Responsável por privacidade: Bruno, interino; designação formal obrigatória antes da homologação  
> Atualizado em: 2026-07-29  
> Origem: `spec/01-prd.md` a `spec/07-roadmap-criterios-aceite.md`

## Contexto

Visitantes encontram informações turísticas fragmentadas e nem sempre atualizadas. Negócios e comunidades locais aparecem fora da jornada real do turista. A operação precisa publicar inventários confiáveis, manter histórico e medir conexões sem rastreamento excessivo.

O MVP valida a ECOnexão no eixo Santarém-Alter do Chão, começando pela rota de Pindobal e usando uma arquitetura que aceite outras regiões sem reconstrução.

## Escopo incluído

- PWA pública com seleção de região, rotas, detalhe, mapa, catálogo e conteúdo offline seletivo.
- Perfil e preferências locais sem conta obrigatória.
- Painel editorial com papéis, importação CSV, revisão, publicação, rollback e auditoria.
- APIs públicas e administrativas versionadas.
- Analytics próprio, pseudonimizado e condicionado ao consentimento.
- Temas claro e escuro com a identidade visual ECOnexão.

## Fora do escopo

Reservas e pagamentos, avaliações públicas, conta obrigatória, aplicativos nativos, rastreamento contínuo, navegação curva a curva, publicação autônoma por IA e expansão territorial antes da validação do método.

## Histórias e critérios de aceite

### RF-01 - Seleção de região

**História:** Como visitante, quero selecionar e trocar a região para explorar apenas conteúdo relevante ao território escolhido.

1. QUANDO o visitante abrir um link com região válida O SISTEMA DEVE ativar essa região.
2. QUANDO não houver região no link O SISTEMA DEVE usar a preferência local válida ou solicitar escolha.
3. QUANDO a região mudar O SISTEMA DEVE atualizar rotas, mapa e catálogo sem misturar registros de outras regiões.
4. SE a região estiver indisponível O SISTEMA DEVE explicar o estado e oferecer regiões publicadas.

### RF-02 - Descoberta de rotas

**História:** Como visitante, quero buscar e filtrar rotas publicadas para escolher uma experiência adequada.

1. QUANDO uma região estiver ativa O SISTEMA DEVE listar somente rotas publicadas dessa região.
2. QUANDO filtros forem aplicados O SISTEMA DEVE atualizar resultados e expor uma forma de limpar os filtros.
3. SE não houver resultado O SISTEMA DEVE mostrar um estado vazio útil sem remover a região ativa.
4. QUANDO um card for acionado O SISTEMA DEVE abrir a rota correta por URL compartilhável.

### RF-03 - Experiência da rota

**História:** Como visitante, quero compreender, preparar e percorrer uma rota com informações confiáveis.

1. QUANDO uma rota publicada for aberta O SISTEMA DEVE apresentar visão geral, etapas, preparação, alertas e data de verificação.
2. QUANDO o visitante alternar entre Visão geral, Mapa e Catálogo O SISTEMA DEVE preservar a rota e os filtros relevantes.
3. QUANDO houver mapa O SISTEMA DEVE oferecer as mesmas informações essenciais em lista textual.
4. SE um alerta crítico estiver vigente O SISTEMA DEVE destacá-lo antes de ações que iniciem o percurso.

### RF-04 - Mapa e localização opcional

**História:** Como visitante, quero visualizar pontos e minha proximidade sem ser obrigado a compartilhar localização.

1. QUANDO o mapa abrir O SISTEMA DEVE funcionar sem permissão de localização.
2. QUANDO o visitante solicitar “usar minha localização” O SISTEMA DEVE explicar a finalidade antes da permissão do sistema.
3. SE a permissão for negada O SISTEMA DEVE manter mapa, lista e navegação externa utilizáveis.
4. ENQUANTO a localização estiver ativa O SISTEMA NÃO DEVE enviar coordenadas precisas ao backend no MVP.
5. QUANDO a rota possuir atores publicados com localização pública O SISTEMA DEVE exibi-los como pins no mapa e na lista textual equivalente.
6. QUANDO houver muitos pins próximos O SISTEMA DEVE agrupá-los visualmente e permitir ampliar o agrupamento sem ocultar a contagem.
7. QUANDO o visitante filtrar uma categoria O SISTEMA DEVE atualizar mapa, contagem e lista com o mesmo conjunto de pontos.
8. SE um candidato ainda estiver em rascunho, não verificado ou em quarentena Google O SISTEMA NÃO DEVE exibi-lo no mapa público.

### RF-05 - Catálogo e conexões

**História:** Como visitante, quero encontrar empresas, prestadores, comunidades e pontos de apoio relacionados à rota.

1. QUANDO a aba Catálogo abrir O SISTEMA DEVE listar apenas atores publicados e vinculados à rota.
2. QUANDO um ator for aberto O SISTEMA DEVE mostrar contatos autorizados, atualização e contexto na rota.
3. QUANDO o visitante acionar WhatsApp, ligação, site ou “como chegar” O SISTEMA DEVE abrir o destino externo correto.
4. QUANDO houver consentimento de analytics O SISTEMA DEVE registrar intenção de contato, nunca venda confirmada.

### RF-06 - Uso local e offline

**História:** Como visitante, quero guardar preferências e o núcleo de uma rota para usar o produto em conectividade limitada.

1. QUANDO o visitante favoritar ou ajustar preferências O SISTEMA DEVE persistir os dados somente no dispositivo no MVP.
2. QUANDO o visitante solicitar download de uma rota O SISTEMA DEVE informar tamanho, conteúdo e estado da operação.
3. SE a rede cair após o download O SISTEMA DEVE manter acessíveis resumo, etapas, alertas baixados e catálogo essencial.
4. QUANDO houver versão nova O SISTEMA DEVE informar que o pacote está desatualizado e permitir atualização.

### RF-07 - Identidade visual e temas

**História:** Como usuário, quero escolher tema claro ou escuro para usar a ECOnexão com conforto e reconhecer sua identidade.

1. QUANDO não houver escolha salva O SISTEMA DEVE respeitar `prefers-color-scheme`, mantendo o tema claro como linguagem visual principal.
2. QUANDO o usuário trocar o tema O SISTEMA DEVE aplicar a mudança imediatamente e persistir a preferência local.
3. EM AMBOS os temas O SISTEMA DEVE usar tokens semânticos derivados da paleta oficial e manter contraste WCAG 2.2 AA.
4. QUANDO o tema mudar O SISTEMA DEVE atualizar controles, mapas, gráficos e `theme-color` sem depender apenas de cor para comunicar estado.

### RF-08 - Operação editorial

**História:** Como equipe editorial, quero criar, revisar e publicar conteúdo com segregação de responsabilidades.

1. QUANDO um editor salvar conteúdo O SISTEMA DEVE criar rascunho sem publicá-lo.
2. QUANDO um revisor devolver conteúdo O SISTEMA DEVE exigir motivo e preservar o histórico.
3. QUANDO um publicador aprovar uma versão válida O SISTEMA DEVE publicá-la atomicamente.
4. SE houver informação crítica vencida O SISTEMA DEVE bloquear a publicação ou exigir confirmação autorizada e auditada.
5. QUANDO uma pessoa sem sessão administrativa válida acessar um recurso protegido O SISTEMA DEVE negar o acesso sem revelar dados operacionais.
6. QUANDO uma sessão administrativa executar login, logout ou outra operação mutável O SISTEMA DEVE exigir proteção CSRF válida.

### RF-09 - Importação CSV

**História:** Como editor, quero importar catálogo em volume e corrigir erros antes da revisão.

1. QUANDO um CSV for enviado O SISTEMA DEVE validar cabeçalhos, tipos, relações, duplicidades e campos obrigatórios.
2. SE houver erro O SISTEMA DEVE indicar linha, coluna, código e orientação sem importar parcialmente.
3. QUANDO a pré-validação passar O SISTEMA DEVE mostrar o resumo das mudanças antes da confirmação.
4. QUANDO a importação for confirmada O SISTEMA DEVE criar rascunhos e registrar arquivo, autor e resultado.
5. QUANDO um inventário histórico e seu complemento operacional forem adequados O SISTEMA DEVE unir as linhas correspondentes sem duplicar registros presentes nas duas fontes.
6. SE campos compartilhados das duas fontes divergirem para o mesmo registro O SISTEMA DEVE bloquear a adequação e identificar registro, campo e valores conflitantes.
7. QUANDO houver possível duplicidade por identificador, nome, endereço ou proximidade O SISTEMA DEVE registrá-la no relatório de revisão manual antes da importação.
8. SE a proveniência declarar Google Maps ou Google Places O SISTEMA NÃO DEVE copiar a linha para o CSV editorial e DEVE colocá-la em quarentena para verificação independente.
9. QUANDO a adequação terminar O SISTEMA DEVE produzir um CSV no schema oficial e um relatório separado com totais, exclusões e motivos de revisão.

### RF-10 - Versionamento, rollback e auditoria

**História:** Como publicador ou administrador, quero rastrear e restaurar versões para operar o catálogo com segurança.

1. QUANDO conteúdo for publicado O SISTEMA DEVE registrar versão imutável, autor, data e diferenças.
2. QUANDO um rollback for solicitado O SISTEMA DEVE criar nova publicação baseada na versão escolhida, sem apagar o histórico.
3. QUANDO ocorrer ação administrativa crítica O SISTEMA DEVE registrar ator, alvo, ação, data e metadados seguros.
4. O SISTEMA NÃO DEVE permitir que o mesmo usuário burle a segregação definida para revisão e publicação.

### RF-11 - Analytics e privacidade

**História:** Como visitante, quero controlar analytics; como operação, quero métricas agregadas de uso e conexão.

1. ENQUANTO não houver consentimento opcional O SISTEMA NÃO DEVE coletar eventos dessa finalidade.
2. QUANDO o consentimento for revogado O SISTEMA DEVE interromper novos eventos opcionais imediatamente.
3. QUANDO eventos forem recebidos O SISTEMA DEVE validar nomes e propriedades por allowlist.
4. O SISTEMA NÃO DEVE receber coordenadas, textos livres, telefones, mensagens ou replay de sessão nos eventos.
5. QUANDO um analista abrir o dashboard O SISTEMA DEVE priorizar agregados e aplicar limites contra reidentificação.

### RF-12 - Relato de informação incorreta

**História:** Como visitante, quero informar um dado incorreto para ajudar a manter a rota confiável.

1. QUANDO um relato for enviado O SISTEMA DEVE vinculá-lo ao registro e criar uma solicitação de revisão.
2. O SISTEMA NÃO DEVE publicar automaticamente a correção sugerida.
3. SE o relato contiver conteúdo inválido ou abusivo O SISTEMA DEVE rejeitá-lo com resposta segura.

### RF-13 - Descoberta assistida de pontos no Google Maps

**História:** Como editor, quero consultar pontos próximos a uma rota no Google Maps para descobrir candidatos que ainda precisarão de verificação editorial.

1. QUANDO um editor executar a descoberta com credencial configurada O SISTEMA DEVE consultar a Places API para uma área, tipos e limite explícitos.
2. QUANDO houver resultados O SISTEMA DEVE apresentá-los como prévia temporária, com atribuição ao Google Maps, sem publicá-los ou vinculá-los automaticamente ao catálogo.
3. O SISTEMA NÃO DEVE persistir conteúdo retornado pela Places API além das exceções permitidas; Place IDs podem ser guardados como referência de origem.
4. SE a credencial estiver ausente ou a API falhar O SISTEMA DEVE encerrar com orientação segura, sem revelar a chave, resposta sensível ou criar estado parcial.
5. QUANDO um candidato for aproveitado O SISTEMA DEVE exigir criação ou edição humana de rascunho e verificação das informações em fonte autorizada antes da publicação.
6. ENQUANTO a integração estiver indisponível O SISTEMA DEVE manter todas as funções públicas e o fluxo editorial manual utilizáveis.
7. ANTES de disponibilizar a prévia em interface gráfica O SISTEMA DEVE aplicar atribuição visual, termos, privacidade, autenticação, cota e orçamento compatíveis com o provedor.
8. QUANDO uma consulta concluída for registrada O SISTEMA DEVE persistir somente o Place ID, os parâmetros próprios da consulta, posição no resultado e metadados operacionais, sem copiar nome, endereço, contato, avaliação, fotografia, URI ou coordenadas retornadas pelo Google.
9. QUANDO a mesma consulta ou candidato reaparecer O SISTEMA DEVE atualizar o histórico de ocorrência de forma idempotente, preservando decisões editoriais anteriores.
10. QUANDO candidatos forem apresentados offline O SISTEMA DEVE usar exclusivamente campos editoriais próprios, associados a fonte autorizada e revisão humana; o Place ID pode aparecer apenas como referência técnica.

## Requisitos não funcionais

### RNF-01 - Acessibilidade

- Fluxos essenciais devem atender WCAG 2.2 nível AA, ser operáveis por teclado e ter alternativa textual para mapas.

### RNF-02 - Desempenho

- Páginas públicas prioritárias devem buscar Core Web Vitals “bom” no percentil 75 em dispositivos móveis. O orçamento inicial deve ser registrado antes da implementação e revalidado com dados reais da fatia vertical.

### RNF-03 - Segurança

- Sessões administrativas, autorização por objeto, rate limiting, validação de arquivos, proteção CSRF e auditoria devem ser testados.

### RNF-04 - Privacidade

- Minimização, finalidade, retenção e direitos do titular seguem `spec/06-analytics-lgpd.md`; logs não recebem dados pessoais desnecessários.

### RNF-05 - Confiabilidade

- Publicações são atômicas; importações são idempotentes por arquivo e lote; falhas não deixam estado público parcial.

### RNF-06 - Portabilidade multirregional

- Nenhuma regra de domínio depende de uma região fixa; adicionar uma região publicada não exige alteração de código.

### RNF-07 - Observabilidade

- Erros, jobs e publicação devem ser rastreáveis por IDs técnicos, sem conteúdo pessoal nos logs.

### RNF-08 - Governança de serviços externos

- Integrações faturáveis devem ter credenciais server-side restritas, cotas, orçamento, alertas, atribuição e modo degradado documentados; falhas externas não bloqueiam o núcleo público.

## Regras de negócio

- RB-01: uma rota pertence a uma região.
- RB-02: um ator pode participar de várias rotas e ter várias localizações.
- RB-03: uma rota pública referencia somente registros publicados.
- RB-04: arquivamento não apaga histórico.
- RB-05: conteúdo patrocinado deve ser identificado.
- RB-06: CSV, bot e IA criam rascunhos ou solicitações; um humano publica.
- RB-07: uma interação externa mede intenção, não transação confirmada.
- RB-08: resultados de fontes externas são candidatos de curadoria; somente humanos transformam dados verificados em rascunhos publicáveis.

## Decisões aprovadas para a fundação

- [x] Next.js App Router e TypeScript estrito para a PWA e o painel.
- [x] MapLibre GL JS com GeoJSON e provedor de tiles configurável por ambiente.
- [x] Offline inicial limitado a dados, manifestos e mídia essencial por rota; cache amplo de tiles fica fora do primeiro corte.
- [x] Monorepo com `pnpm` para TypeScript, `uv` para Python e serviços locais reproduzíveis.
- [x] Supabase em `sa-east-1` como PostgreSQL/PostGIS do desenvolvimento e piloto; somente a API Django usa a conexão SQL.
- [x] Desenvolvimento local sem Docker: API executada com `uv` contra o Supabase; hospedagem da API/frontend e mídia compatível com S3/CDN permanecem como portão de homologação.
- [x] Bruno assume interinamente produto e privacidade durante a fundação; a designação formal de privacidade permanece obrigatória antes da homologação.
- [x] Orçamento inicial: LCP <= 2,5 s, INP <= 200 ms e CLS <= 0,1 no p75 móvel; disponibilidade alvo de 99,5% no piloto; CSV limitado a 10 MiB e mídia a 20 MiB por arquivo.

## Pendências para homologação

- [ ] Contratar e registrar provedores de hospedagem da API/frontend, tiles e mídia/CDN.
- [ ] Formalizar responsável por privacidade, controlador e canal do titular.
- [ ] Validar os orçamentos iniciais com dados reais da fatia vertical de Pindobal.
- [ ] Aprovar termos, privacidade, orçamento, cotas, chave restrita e atribuição antes de ativar Google Places fora do teste técnico local.
