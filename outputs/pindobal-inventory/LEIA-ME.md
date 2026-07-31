# Adequação Santarém–Pindobal — leitura rápida

## Resultado em 30 segundos

- **195 registros** foram reconciliados entre o inventário bruto e o complemento operacional.
- As linhas repetidas entre as duas fontes foram tratadas como o mesmo registro: **não viraram 390**.
- **181 registros** estão no CSV canônico como propostas de rascunho.
- **14 candidatos do Google Maps** foram considerados, mas ficaram em quarentena para verificação independente.
- **0 duplicidades fortes** foram encontradas por nome + endereço/proximidade.
- **9 pares compartilham telefone ou e-mail** e precisam ser avaliados como possível mesmo ator, unidades ou serviços relacionados.
- Nenhum registro foi publicado e nenhum rascunho foi gravado no banco nesta etapa.

## Fontes identificadas dentro dos arquivos

| Proveniência                                            | Registros | Tratamento                                                      |
| ------------------------------------------------------- | --------: | --------------------------------------------------------------- |
| Inventário da Oferta Turística da Secretaria de Turismo |       171 | Elegível para rascunho, sempre não verificado                   |
| Pesquisa Google Maps                                    |        14 | Quarentena; exige fonte independente                            |
| Pesquisa de transporte 2026                             |        10 | Elegível como pesquisa pública, mas exige revisão da referência |

## O que precisa de atenção

Os números abaixo são motivos de revisão; um registro pode aparecer em mais de um grupo.

| Atenção                         | Ocorrências | Próxima ação                                                  |
| ------------------------------- | ----------: | ------------------------------------------------------------- |
| Autorização de contato pendente |         142 | Confirmar antes de exibir telefone, e-mail ou rede social     |
| Sem contato                     |          39 | Buscar ao menos um canal autorizado                           |
| Mais de 500 m da rota           |          35 | Confirmar se o vínculo com Pindobal faz sentido               |
| Google Maps em quarentena       |          14 | Verificar diretamente ou em fonte independente                |
| Sem endereço                    |          10 | Confirmar endereço ou atendimento móvel                       |
| Pares com contato compartilhado |           9 | Decidir se são duplicatas, unidades ou serviços do mesmo ator |
| Sem coordenadas                 |           1 | Georreferenciar ou definir área de atendimento                |

## Antes de importar no banco

O banco já possui a região `santarem-alter-do-chao` e a rota `pindobal`. Das 13 categorias usadas
no CSV adequado, somente `alimentacao` existe atualmente. As outras 12 precisam ser aprovadas e
cadastradas antes da pré-validação:

- `agencia_turismo`
- `artesanato`
- `cartorios`
- `casas_de_temporada`
- `hospedagem`
- `locadora_veiculos`
- `mercado`
- `religioso`
- `servico_publico`
- `servicos_equipamentos_para_eventos`
- `shopping_lojas_de_departamento`
- `transporte`

## Ordem recomendada de trabalho

1. Abrir `revisao-manual-pindobal.csv` e filtrar primeiro `prioridade = bloqueante`.
2. Resolver os 14 candidatos Google e os 9 pares com contato compartilhado.
3. Aprovar ou ajustar as 12 categorias ausentes.
4. Revisar `prioridade = alta`, começando por contatos, segurança e transporte.
5. Corrigir o CSV canônico conforme as decisões editoriais.
6. Enviar o CSV corrigido à aba **Importar CSV** do painel.
7. Confirmar o lote; ele criará somente rascunhos privados.

## Arquivos desta entrega

- `catalogo-pindobal-adequado.csv`: arquivo no schema oficial, pronto para correção e pré-validação.
- `revisao-manual-pindobal.csv`: fila completa de atenção, com motivo e ação recomendada.
- `resumo-pindobal.json`: hashes, contagens por fonte, categoria e motivo.
