# Estrutura do repositório

Estrutura-alvo:

```text
apps/
├── web/             # PWA pública
└── admin/           # painel operacional
services/
└── api/             # Django, domínio e APIs
packages/
├── ui/              # componentes e tokens compartilhados
├── contracts/       # tipos e contratos gerados
└── config/          # configurações compartilhadas
spec/                # documentação detalhada do produto
.kiro/
├── steering/        # contexto permanente
├── templates/       # modelos de spec
└── specs/           # specs executáveis
```

Enquanto a implementação não existir, não crie diretórios vazios. A tarefa de fundação deve registrar as decisões definitivas de monorepo, gerenciador de pacotes e execução local.

## Nomes

- Pastas e código: inglês técnico consistente.
- Conteúdo do produto e documentação: português brasileiro.
- IDs de requisitos: `RF-`, `RNF-`, `RB-`.
- Slugs: minúsculos, ASCII e separados por hífen.
- Tokens visuais: semânticos (`surface`, `text-muted`, `action-primary`), não nomes de telas.

