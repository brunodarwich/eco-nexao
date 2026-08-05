# Operação demonstrativa de Pindobal

Pindobal é a rota vertical de validação do MVP. Os procedimentos abaixo operam rascunhos e
dados demonstrativos; nenhum deles autoriza publicação automática.

## Dados demonstrativos

Para criar ou atualizar a demonstração no banco configurado localmente:

```powershell
pnpm seed:pindobal
```

O script cria ou atualiza somente rascunhos demonstrativos e preserva conteúdo já publicado.
Publicação exige o workflow editorial, confirmação humana e auditoria. Confirme o ambiente e a
conexão antes de executá-lo.

## Adequação do inventário

Entradas atuais:

- `data/pindobal/santarem-pindobal.csv`: inventário bruto;
- `data/pindobal/pontos_interesse.csv`: complemento operacional.

Execute:

```powershell
uv --cache-dir .uv-cache run --project services/api python services/api/manage.py adapt_pindobal_inventory --raw data/pindobal/santarem-pindobal.csv --operational data/pindobal/pontos_interesse.csv --output-dir outputs/pindobal-inventory
```

Saídas:

- `catalogo-pindobal-adequado.csv`: CSV canônico para pré-validação;
- `revisao-manual-pindobal.csv`: itens que exigem decisão humana;
- `resumo-pindobal.json`: hashes, fontes, categorias e contagens;
- `LEIA-ME.md`: resumo operacional da execução.

O adaptador não escreve no banco. Envie somente o CSV canônico para **Importar CSV**; a
confirmação cria rascunhos privados. Revise fonte, região, rota, categoria e alertas antes de
qualquer publicação.

## Descoberta editorial pelo Google Places

Com a Places API (New) habilitada e `GOOGLE_MAPS_API_KEY` configurada apenas no backend:

```powershell
pnpm discover:pindobal
```

A resposta é uma prévia efêmera e atribuída. Não redirecione a saída para arquivo, não use os
dados diretamente no mapa público e não os inclua no pacote offline. Somente conteúdo próprio,
verificado por pessoa e por fonte autorizada, pode virar rascunho editorial.

A prévia administrativa permanece desativada por padrão. Sua ativação externa exige chave por
ambiente, restrições, cotas, orçamento, alertas e revisão jurídica. Consulte a
[decisão de curadoria](../../spec/08-google-places-curadoria.md).

## Pacote offline

A PWA pode guardar visão geral, preparo, etapas, alertas e catálogo textual da rota. Não guarda
tiles, localização do visitante nem conteúdo externo. Falhas de armazenamento preservam o
pacote anterior e não interrompem a navegação online.
