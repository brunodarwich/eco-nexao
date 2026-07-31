# Pulso do desenvolvimento ECOnexão

Painel local em Streamlit que transforma os arquivos
`.kiro/specs/**/tasks.md` em orientação de próxima etapa, métricas, Kanban e
visão de bloqueios.

## Executar

Na raiz do repositório:

```powershell
uv --cache-dir .uv-cache sync --project tools/development_dashboard
uv --cache-dir .uv-cache run --project tools/development_dashboard streamlit run tools/development_dashboard/streamlit_app.py
```

Abra `http://localhost:8501`. O painel atualiza automaticamente no intervalo
escolhido e também oferece o botão **Atualizar agora**.

## Fonte de dados

O painel é somente leitura. Para atualizar o estado:

- `[ ]` pendente;
- `[~]` em andamento;
- `[x]` concluída e verificada;
- `[!]` bloqueada, com o motivo na linha indentada seguinte.

## Verificar

```powershell
uv --cache-dir .uv-cache run --project tools/development_dashboard pytest
uv --cache-dir .uv-cache run --project tools/development_dashboard ruff check .
uv --cache-dir .uv-cache run --project tools/development_dashboard ruff format --check .
```
