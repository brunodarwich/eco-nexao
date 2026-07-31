# Tarefas — carga local do inventário de Pindobal

- [x] 1. Implementar comando transacional e idempotente de publicação local
  - _Requisitos: RF-04, RF-05, RF-08, RNF-03, RNF-08_
  - Arquivo: `services/api/modules/imports/management/commands/publish_pindobal_inventory.py`
- [x] 2. Testar confirmação, fontes permitidas e integração com o adaptador
  - Dependência: 1
  - _Requisitos: RF-04, RF-05, RF-08_
  - Arquivo: `services/api/modules/imports/test_publish_pindobal_inventory.py`
  - Verificação: 5 testes isolados aprovados; Ruff aprovado.
- [x] 3. Executar a carga e verificar banco e API pública consumida pelo app
  - Dependência: 2
  - _Requisitos: RF-04, RF-05_
  - Comando: `python manage.py publish_pindobal_inventory --csv
    outputs/pindobal-inventory/catalogo-pindobal-adequado.csv
    --confirm-publish-unverified`
  - Evidência: 181 atores publicados e vinculados à rota, 180 localizações públicas com ponto,
    API pública HTTP 200 com 181 itens/180 pontos e nenhum fixture demonstrativo; Django
    `check`, Ruff e formatação aprovados.
