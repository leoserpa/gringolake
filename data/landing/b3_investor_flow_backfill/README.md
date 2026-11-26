# Backfill Histórico Oficial da B3 (Participação dos Investidores)

A API pública oficial do BDI da B3 (`SharesInvesVolum`) disponibiliza uma janela móvel de **`D-21` pregões**.
O pipeline persiste automaticamente todos os snapshots diários na camada Bronze (`data/bronze/b3_investor_flow_mtd/`), construindo histórico contínuo daqui para frente.

Caso você possua arquivos históricos oficiais do BDI da B3 (anteriores à janela `D-21`) e queira integrá-los à arquitetura Medalhão, salve arquivos `.csv` ou `.parquet` nesta pasta com o seguinte contrato de schema:

| Coluna | Tipo | Obrigatória | Descrição |
| --- | --- | --- | --- |
| `reference_date` | `YYYY-MM-DD` | Sim | Data do pregão de referência (não a data de publicação D+2) |
| `investor_type_raw` | `string` | Sim | Nome oficial B3 (`Investidor Estrangeiro`, `Institucionais`, `Investidores Individuais`, `Instituições Financeiras`, `Outros`) |
| `mtd_purchases_k_brl` | `float` | Sim | Compras acumuladas no mês (MTD) em **R$ mil** |
| `mtd_sales_k_brl` | `float` | Sim | Vendas acumuladas no mês (MTD) em **R$ mil** |
| `publication_date` | `YYYY-MM-DD` | Não | Data de publicação do BDI (default = `reference_date`) |
| `purchase_share_pct` | `float` | Não | Participação % nas compras |
| `sale_share_pct` | `float` | Não | Participação % nas vendas |

Na próxima materialização do asset `bronze/b3_investor_flow_mtd`, os arquivos desta pasta serão ingeridos com rastreabilidade (`_source_system = 'b3_official_backfill'`) e deduplicados automaticamente na camada Silver.
