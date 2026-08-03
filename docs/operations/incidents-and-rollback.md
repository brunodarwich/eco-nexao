# Operação, Backup e Resposta a Incidentes (Pindobal e Multiregião)

Este documento detalha os procedimentos de continuidade, backup, rollback de código/banco, rollback de conteúdo e gestão de incidentes operacionais para a plataforma ECOnexão.

## 1. Backup e Restauração de Banco de Dados

### 1.1 Snapshot de Banco (Desenvolvimento/Homologação)
Em ambientes Django sem PostgreSQL físico configurado, utilize o barramento nativo de serialização para backup de instâncias:

```powershell
# Gerar backup JSON das tabelas principais de regiões e rotas
uv --cache-dir .uv-cache run --project services/api python services/api/manage.py dumpdata regions routes publishing catalog --format json -o outputs/backup-latest.json
```

### 1.2 Restauração de Dados
Para restaurar os dados de um snapshot limpo em caso de indisponibilidade ou teste:

```powershell
# Carregar fixture/backup previamente gerado
uv --cache-dir .uv-cache run --project services/api python services/api/manage.py loaddata outputs/backup-latest.json
```

---

## 2. Rollback de Aplicação (Código e Migrações)

### 2.1 Reversão de Código
Todo o repositório segue a regra de commits atômicos e tag de releases imutáveis:
1. Identifique o hash da release anterior no histórico do Git.
2. Execute o rollback de implantação no provedor de hospedagem ou faça o checkout da tag estável anterior.

### 2.2 Reversão de Migrações (Database Schema Rollback)
Todas as migrações dos módulos `accounts`, `audit`, `catalog`, `core`, `publishing`, `regions` e `routes` são reversíveis e declarativas:

```powershell
# Reverter a última migração aplicada no módulo de publishing
uv --cache-dir .uv-cache run --project services/api python services/api/manage.py migrate publishing <NOME_DA_MIGRACAO_ANTERIOR>
```

---

## 3. Rollback de Conteúdo Editorial

### 3.1 Arquitetura de Versões Imutáveis
O módulo `publishing` gera snapshots imutáveis (`PublicationVersion`) vinculados a checksums SHA-256 e logs de auditoria (`AuditEvent`). A versão publicada atual do aplicativo **nunca** é sobrescrita destrutivamente; o rollback gera um novo número de versão incrementado (ex: v1 -> v2 (com falha) -> v3 (restauração da v1)).

### 3.2 Executando Rollback de Conteúdo
O rollback de um item publicado para uma versão anterior pode ser realizado via API administrativa ou serviço backend:

- **Via Painel Admin / API:**
  `POST /api/v1/admin/editorial/publications/{publication_id}/restore`
  - Requer autorização `AdminAction.PUBLISH`.
  - Exige confirmação humana, de fonte e motivo explicitado.
  - Exige `expected_current_version` para evitar conflito com edições concorrentes.

---

## 4. Resposta a Incidentes e Matriz de Mitigação

| Tipo de Incidente | Causa Provável | Ação de Mitigação Implicada |
| :--- | :--- | :--- |
| **Inconsistência de Conteúdo** | Dados de rota/região publicados com erros | Acionar `restorePublicationVersion` para a última versão estável |
| **Conflito de Edição Concorrente** | Dois editores alterando o mesmo item simultaneamente | O sistema retorna HTTP 409 (`publication_conflict`). O editor deve recarregar a versão mais recente antes de aplicar alterações |
| **Falha em Migração de Banco** | Script de migração com erro em produção | Executar o comando de rollback de migração (`python manage.py migrate <app> <previous_migration>`) e reverter o deployment de código |
| **Suspeita de Vazamento de Dados / PII** | Dados pessoais não autorizados em rascunhos | Acionar a API de LGPD/Auditoria para purga/anonimização e registrar o incidente em `AuditEvent` |
