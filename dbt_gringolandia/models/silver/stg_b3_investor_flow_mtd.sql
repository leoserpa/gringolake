with raw_flow as (
    select
        cast(publication_date as date) as publication_date,
        cast(reference_date as date) as reference_date,
        trim(cast(investor_type_raw as varchar)) as investor_type_raw,
        cast(mtd_purchases_k_brl as double) as mtd_purchases_k_brl,
        cast(purchase_share_pct as double) as purchase_share_pct,
        cast(mtd_sales_k_brl as double) as mtd_sales_k_brl,
        cast(sale_share_pct as double) as sale_share_pct,
        cast(source_note_pt as varchar) as source_note_pt,
        cast(_source_system as varchar) as _source_system,
        cast(_ingested_at as timestamptz) as _ingested_at
    from {{ source('bronze', 'b3_investor_flow_mtd') }}
    where reference_date is not null
      and investor_type_raw is not null
),

standardized as (
    select
        publication_date,
        reference_date,
        investor_type_raw,
        case
            when lower(investor_type_raw) like '%estrangeiro%' then 'estrangeiro'
            when lower(investor_type_raw) = 'institucionais' then 'institucional'
            when lower(investor_type_raw) like '%individuais%'
              or lower(investor_type_raw) like '%pessoa f%' then 'pessoa_fisica'
            when lower(investor_type_raw) like '%financeira%' then 'instituicoes_financeiras'
            when lower(investor_type_raw) like '%outro%' then 'outros'
            else 'desconhecido'
        end as investor_type_code,
        mtd_purchases_k_brl,
        purchase_share_pct,
        mtd_sales_k_brl,
        sale_share_pct,
        source_note_pt,
        _source_system,
        _ingested_at
    from raw_flow
),

deduplicated as (
    select
        reference_date,
        publication_date,
        investor_type_code,
        investor_type_raw,
        mtd_purchases_k_brl,
        purchase_share_pct,
        mtd_sales_k_brl,
        sale_share_pct,
        (mtd_purchases_k_brl - mtd_sales_k_brl) as mtd_net_flow_k_brl,
        round((mtd_purchases_k_brl - mtd_sales_k_brl) / 1000000.0, 6) as mtd_net_flow_bi_brl,
        source_note_pt,
        _source_system,
        _ingested_at,
        row_number() over (
            partition by reference_date, investor_type_code
            order by
                case when _source_system = 'b3_bdi_api' then 0 else 1 end asc,
                publication_date desc,
                _ingested_at desc
        ) as rn
    from standardized
)

select
    cast(reference_date as varchar) || '_' || investor_type_code as investor_flow_mtd_sk,
    reference_date,
    publication_date,
    investor_type_code,
    investor_type_raw,
    mtd_purchases_k_brl,
    purchase_share_pct,
    mtd_sales_k_brl,
    sale_share_pct,
    mtd_net_flow_k_brl,
    mtd_net_flow_bi_brl,
    source_note_pt,
    _source_system,
    _ingested_at
from deduplicated
where rn = 1
order by reference_date, investor_type_code
