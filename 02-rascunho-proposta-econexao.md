# Proposta preliminar — ECOnexão

> **Versão:** 0.1  
> **Data:** 27 de julho de 2026  
> **Status:** rascunho para alinhamento entre sócios e apresentação inicial a parceiros  
> **Território de validação:** Santarém, Alter do Chão e rotas selecionadas do Tapajós  
> **Próximas expansões planejadas:** Altamira e Belém

## 1. Apresentação

A **ECOnexão** é uma plataforma digital criada para tornar a descoberta e a experiência turística mais simples, confiável e conectada a cada território.

O projeto organiza rotas, informações práticas, empreendimentos, comunidades e serviços de apoio em uma jornada única. Assim, o visitante consegue entender o destino, preparar o deslocamento, percorrer uma rota e entrar em contato com atores locais sem depender de pesquisas fragmentadas em diferentes canais.

Ao mesmo tempo, a plataforma amplia a visibilidade de negócios e iniciativas comunitárias, ajuda a gerar contatos qualificados e transforma o inventário turístico existente em uma base viva, atualizável e orientada ao uso.

Embora o primeiro MVP seja validado no eixo Santarém–Alter do Chão, a ECOnexão não será apresentada como um aplicativo exclusivo do Tapajós. Regiões, rotas e catálogos serão entidades independentes, permitindo a expansão planejada para Altamira, Belém e outros destinos sem reconstruir o produto.

## 2. Contexto e oportunidade

O Tapajós reúne natureza, praias, rios, cultura, gastronomia e experiências comunitárias com forte potencial turístico. Apesar dessa riqueza, grande parte da informação necessária para planejar uma visita ainda está distribuída entre sites institucionais, mecanismos de busca, redes sociais, aplicativos de mensagem e indicações pessoais.

Essa fragmentação cria três oportunidades:

1. oferecer ao turista informações práticas e confiáveis em uma experiência simples;
2. inserir empreendedores e comunidades dentro de rotas e jornadas completas, e não apenas em listas;
3. apoiar a gestão do destino com uma base estruturada, rastreável e continuamente atualizada.

A existência do Inventário da Oferta Turística de Santarém reduz o custo de partida. A ECOnexão poderá organizar, enriquecer e validar esses dados, sem substituir o trabalho institucional nem apresentar automaticamente como atuais informações que ainda não tenham sido confirmadas.

## 3. Problema

O turista encontra dificuldade para responder, em um único lugar, perguntas essenciais:

- Qual rota combina com meu tempo, orçamento e perfil?
- Como chegar e retornar?
- Quanto tempo dura e quanto pode custar?
- O que devo levar?
- Onde encontro alimentação, hospedagem, transporte, saúde e segurança?
- Quais serviços e experiências são confiáveis?
- O que fazer se a conexão com a internet falhar?

Do outro lado, muitos empreendedores, guias e comunidades têm presença digital limitada ou aparecem de forma isolada. Mesmo quando recebem contatos, raramente conseguem identificar a origem da oportunidade ou avaliar o retorno de sua presença em diferentes canais.

## 4. Solução proposta

A ECOnexão será um **guia digital acionável de rotas turísticas**. Cada rota combinará narrativa, preparação, mapa, etapas, atores locais, pontos de apoio, riscos e contatos úteis.

A experiência será organizada em três momentos:

### Descobrir

O visitante conhece o território, compara rotas e escolhe uma experiência compatível com seu interesse, tempo e condição de deslocamento.

### Preparar

Antes de sair, consulta acesso, retorno, duração, dificuldade, custos estimados, formas de pagamento, clima, conectividade, itens necessários e alertas.

### Percorrer

Durante a experiência, acompanha as etapas, consulta mapa ou lista, identifica pontos de apoio e entra em contato com os atores locais.

## 5. Proposta de valor

### Para o turista

Informação confiável para descobrir, preparar e percorrer experiências em diferentes regiões, com contexto local, apoio à segurança e acesso rápido a serviços relevantes.

### Para empreendedores, guias e comunidades

Visibilidade no momento da decisão, presença contextualizada dentro das rotas e geração mensurável de contatos, respeitando a autonomia e o benefício econômico local.

### Para instituições e gestores do destino

Uma camada digital atualizável sobre a oferta turística, com indicadores agregados de interesse e interação que possam apoiar promoção, planejamento e melhoria contínua.

## 6. Público inicial

O usuário prioritário será o **turista brasileiro independente ou semidependente** que planeja a viagem pela internet e utiliza Google, Instagram e WhatsApp para tomar decisões.

Também serão atendidos:

- turistas estrangeiros, inicialmente com preparação estrutural para futura tradução;
- moradores e visitantes regionais;
- recepcionistas, condutores e agentes que recomendam experiências;
- empreendedores, organizações comunitárias e instituições responsáveis pela oferta turística.

## 7. Produto mínimo viável

O produto inicial será uma **aplicação web responsiva e instalável como PWA**, apoiada por um backend modular em Python. Essa escolha reduz a barreira de acesso, permite compartilhamento por link ou QR Code e acelera a validação antes do investimento em aplicativos nativos.

### Entregas do MVP

- página inicial com região atual e rotas em destaque;
- tela de rotas com filtros e cards;
- catálogo com cinco rotas no território inicial;
- Rota de Pindobal como primeira rota-modelo;
- página detalhada de cada rota com abas de visão geral, mapa e catálogo;
- preparação, percurso, etapas e mapa;
- pontos de apoio e atores vinculados;
- alertas, riscos e alternativas;
- links de contato e compartilhamento;
- perfil local e configurações, sem login obrigatório;
- conteúdo essencial disponível offline;
- relato de informação incorreta;
- analytics de comportamento pseudonimizados e controlados por preferência;
- dashboard de produto, conteúdo e conversão;
- painel protegido para cadastro, importação CSV, revisão, publicação e auditoria.

Pindobal será usada para provar o método completo. As demais rotas serão incorporadas com a mesma estrutura somente depois de terem delimitação, fontes, responsáveis e critérios mínimos de prontidão.

### Itens que não fazem parte do primeiro ciclo

- reservas, pagamentos e marketplace;
- aplicativos nativos;
- conta online ou sincronização do perfil entre aparelhos;
- comentários e avaliações públicas;
- programa de fidelidade;
- rastreamento contínuo de localização;
- publicação de Altamira e Belém antes da validação do método no território inicial.

Essas possibilidades permanecem na visão de longo prazo e deverão entrar apenas depois da validação de uso, operação e modelo de receita.

## 8. Modelo de negócio

A ECOnexão terá um modelo **B2B2C**, com uma frente institucional **B2G**. O acesso do turista será gratuito, enquanto a receita virá progressivamente de serviços prestados aos atores da cadeia turística e aos parceiros do destino.

### Fontes de receita propostas

1. **Pilotos e projetos institucionais:** apoio à estruturação, atualização e promoção digital das rotas.
2. **Planos profissionais:** ferramentas de atualização, presença ampliada, indicadores e geração de contatos para parceiros.
3. **Patrocínio de rotas e ações:** presença identificada de marcas e instituições, sem interferir na curadoria.
4. **Inteligência e relatórios agregados:** leitura de procura e interação, respeitando privacidade e finalidade.
5. **Licenciamento futuro:** adoção da tecnologia e metodologia por outros destinos.
6. **Transações futuras:** reservas e comissões somente quando houver rastreabilidade, regras comerciais e capacidade de suporte.

No piloto, recomenda-se evitar mensalidades sem entrega mensurável e não cobrar comissão por simples clique no WhatsApp. O modelo pago deve estar associado a benefícios concretos e evidências de valor.

## 9. Diferenciais

- foco em rotas e jornadas completas;
- integração entre turismo, serviços, saúde, segurança e transporte;
- informação com fonte e data de verificação;
- conexão com o inventário turístico e o ecossistema local;
- funcionamento essencial em condições de baixa conectividade;
- mensuração de ações qualificadas, e não apenas visualizações;
- inclusão de empreendedores e comunidades menos digitalizados;
- metodologia replicável para novas rotas e, futuramente, novos destinos.

## 10. Parcerias necessárias

A construção da ECOnexão depende de cooperação entre setor público, iniciativa privada e comunidades.

São parceiros prioritários:

- Secretaria Municipal de Turismo;
- empreendedores, guias, transportadores e operadores;
- hotéis, pousadas, restaurantes e pontos de apoio;
- comunidades e organizações de Turismo de Base Comunitária;
- Sebrae, universidades e entidades do Sistema S;
- canais de divulgação, eventos e patrocinadores alinhados ao território.

As contrapartidas poderão incluir confirmação de dados, apoio à pesquisa, produção de conteúdo, divulgação, distribuição por QR Code e apoio logístico. Toda presença patrocinada deverá ser identificada e separada da decisão editorial.

## 11. Operação e governança

A confiança será um componente central do produto. Cada informação deverá registrar, quando aplicável:

- fonte;
- responsável;
- data da última confirmação;
- método de validação;
- prazo ou gatilho de revisão;
- autorização de uso de dados e mídia.

Informações de segurança, saúde, transporte, horários e condições de acesso terão prioridade de revisão. Relatos de erro deverão ser triados rapidamente, e alertas críticos poderão causar a suspensão temporária de uma rota ou informação.

A coleta de dados de uso será mínima, transparente e pseudonimizada. A localização só será acessada depois de uma ação e da autorização do usuário, sem rastreamento contínuo por padrão.

## 12. Estratégia de implantação

### Fase 1 — alinhamento e preparação

- confirmar promessa da marca e responsáveis;
- delimitar as cinco rotas;
- fechar o padrão de dados e critérios de prontidão;
- definir piloto, canais e parceiros iniciais.

### Fase 2 — Rota de Pindobal

- pesquisar e estruturar a rota;
- confirmar informações com fontes registradas;
- cadastrar atores e pontos de apoio;
- testar conteúdo, mapa, modo offline e relatos;
- executar piloto controlado.

### Fase 3 — replicação

- corrigir o método a partir de Pindobal;
- cadastrar e testar as rotas 2 a 5 em ondas;
- medir o esforço de replicação;
- publicar somente rotas que atinjam o padrão mínimo.

### Fase 4 — lançamento e validação comercial

- distribuir por redes, parceiros, hotéis, eventos e QR Codes;
- acompanhar o funil de uso;
- entrevistar turistas e parceiros;
- testar planos e contrapartidas comerciais;
- decidir sobre expansão, tradução e novas funcionalidades.

Os rascunhos registram **25 de agosto de 2026** como marco desejado. A data deve ser tratada como meta condicionada à prontidão, especialmente à confirmação dos dados críticos e ao funcionamento da experiência offline.

## 13. Indicadores de sucesso

A métrica principal será a quantidade de **conexões qualificadas por visitante ativo**, como:

- abertura de WhatsApp;
- ligação;
- solicitação de instruções de chegada;
- clique para reserva externa;
- contato com ponto de apoio ou ator local.

Também serão acompanhados:

- acesso e origem do visitante;
- abertura e ativação das rotas;
- salvamentos, compartilhamentos e downloads offline;
- funcionamento do pacote offline;
- utilidade percebida;
- contatos por rota e por categoria;
- correção e atualidade dos dados;
- parceiros ativos e conversão para planos pagos;
- distribuição dos resultados entre negócios e comunidades.

Visualização ou clique representarão intenção, não venda confirmada.

## 14. Riscos e mitigação

| Risco | Resposta proposta |
|---|---|
| Escopo excessivo | Manter o foco em descobrir, preparar e percorrer rotas |
| Dados desatualizados | Registrar fonte, responsável, data e gatilhos de revisão |
| Rotas incompletas | Publicar somente após critérios mínimos de prontidão |
| Falha de internet | Disponibilizar o núcleo da rota offline |
| Patrocínio afetar a confiança | Identificar conteúdo patrocinado e separar comercial de editorial |
| Baixa adesão de parceiros | Oferecer piloto e demonstrar contatos e métricas antes da cobrança |
| Complexidade jurídica de reservas | Adiar transações até existir estrutura comercial e operacional |
| Pouco uso inicial | Testar distribuição assistida antes de concluir que o produto falhou |

## 15. Recursos a definir

Para transformar este rascunho em proposta executiva final, ainda precisam ser definidos:

- equipe e dedicação por função;
- orçamento de desenvolvimento, conteúdo, campo, operação e marketing;
- responsáveis pelas cinco rotas;
- parceiros confirmados e suas contrapartidas;
- cronograma revisado;
- formato jurídico e comercial dos pilotos;
- metas comerciais e financeiras;
- política de privacidade, termos de uso e autorizações.

## 16. Próxima decisão recomendada

A próxima reunião dos sócios deve aprovar cinco pontos:

1. promessa da marca;
2. delimitação e responsáveis pelas cinco rotas;
3. critérios para considerar Pindobal pronta para o piloto;
4. responsáveis por produto, tecnologia, conteúdo, comercial e governança;
5. orçamento, canal e formato do primeiro lançamento.

Com essas decisões, este documento poderá evoluir de rascunho conceitual para uma proposta executiva com escopo, responsáveis, cronograma e investimento.
