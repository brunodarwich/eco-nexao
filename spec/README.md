# Especificação do projeto ECOnexão

> **Versão da spec:** 0.3  
> **Data:** 29 de julho de 2026  
> **Status:** fundação técnica aprovada; portões de homologação pendentes

O nome mais usado para o documento de requisitos do produto é **PRD — Product Requirements Document**. Esta pasta divide o PRD e as especificações complementares para que cada decisão possa evoluir sem transformar o projeto em um único arquivo difícil de manter.

## Documentos

| Documento | Conteúdo |
|---|---|
| [01-prd.md](./01-prd.md) | visão, problema, objetivos, públicos, escopo, regras e métricas |
| [02-telas-fluxos-botoes.md](./02-telas-fluxos-botoes.md) | navegação pública, telas, componentes, botões, eventos e estados |
| [03-backend-python-apis.md](./03-backend-python-apis.md) | arquitetura Python, módulos, segurança e contratos de API |
| [04-modelo-dados-csv.md](./04-modelo-dados-csv.md) | entidades, relações, governança e formato da importação CSV |
| [05-painel-dashboard.md](./05-painel-dashboard.md) | operação administrativa, permissões, publicação, importação e indicadores |
| [06-analytics-lgpd.md](./06-analytics-lgpd.md) | taxonomia de eventos, funis, consentimento, retenção e direitos do titular |
| [07-roadmap-criterios-aceite.md](./07-roadmap-criterios-aceite.md) | fases de entrega, prioridades, testes e definição de pronto |
| [08-google-places-curadoria.md](./08-google-places-curadoria.md) | limites, arquitetura, segurança, custos e portões da descoberta editorial |
| [schemas/catalogo-template.csv](./schemas/catalogo-template.csv) | modelo preenchido do CSV de catálogo |

## Decisões consolidadas

| Tema | Decisão |
|---|---|
| Posicionamento | Plataforma de turismo multirregional; não exclusiva do Tapajós |
| Território do MVP | Eixo Santarém–Alter do Chão, com Pindobal como rota-modelo |
| Expansão planejada | Altamira e Belém após validação do método inicial |
| Produto público | PWA responsiva |
| Perfil do turista | Perfil local e configurações, sem login obrigatório no MVP |
| Backend | Monólito modular em Python com Django e Django REST Framework |
| Dados geográficos | PostgreSQL com PostGIS e GeoDjango |
| Frontend | Next.js App Router e TypeScript estrito |
| Monorepo | `pnpm` para TypeScript e `uv` para Python |
| Mapa | MapLibre GL JS com provedor de tiles configurável |
| Banco do piloto | Supabase/PostGIS em `sa-east-1`, acessado somente pela API |
| Administração | Dashboard e painel protegido |
| Carga inicial | Importação de catálogo por CSV com pré-validação e revisão |
| Analytics | Coleta própria, pseudonimizada e separada por finalidade |
| Localização | Sob demanda; sem rastreamento contínuo |
| Futuro WhatsApp/IA | Webhooks e solicitações de alteração já previstos; publicação sempre revisada por humano |
| Google Places | descoberta editorial opcional no backend; prévia efêmera, atribuída e sem dependência pública |

## Legenda

- **Confirmado:** pedido ou decisão já registrado.
- **Recomendado:** direcionamento proposto nesta spec.
- **Pendente:** depende de decisão dos sócios, validação jurídica ou teste.
- **Futuro:** previsto na arquitetura, mas não deve ser implementado no MVP.

## Regra de atualização

Quando uma decisão mudar:

1. atualizar o documento responsável;
2. registrar a mudança no histórico do PRD;
3. revisar impactos em telas, APIs, dados, analytics e critérios de aceite;
4. atualizar a versão da spec;
5. não reutilizar silenciosamente termos ou endpoints que tenham mudado.
