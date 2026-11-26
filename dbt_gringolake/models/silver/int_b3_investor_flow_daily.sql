with mtd_flow as (
    select
        reference_date,
        publication_date,
        investor_type_code,
        investor_type_raw,
        mtd_purchases_k_brl,
        mtd_sales_k_brl,
        mtd_net_flow_k_brl,
        mtd_net_flow_bi_brl,
        purchase_share_pct,
        sale_share_pct,
        _source_system
    from {{ ref('stg_b3_investor_flow_mtd') }}
),

trading_calendar as (
    select
        trading_date,
        trading_month,
        trading_year,
        prev_trading_date,
        trading_day_num_in_month,
        is_first_trading_day_of_month
    from {{ ref('stg_b3_ibov_daily') }}
),

joined as (
    select
        m.reference_date as trading_date,
        cal.trading_month,
        cal.trading_year,
        cal.prev_trading_date,
        cal.trading_day_num_in_month,
        cal.is_first_trading_day_of_month,
        m.publication_date,
        m.investor_type_code,
        m.investor_type_raw,
        m.mtd_purchases_k_brl,
        m.mtd_sales_k_brl,
        m.mtd_net_flow_k_brl,
        m.mtd_net_flow_bi_brl,
        m.purchase_share_pct,
        m.sale_share_pct,
        m._source_system,
        lag(m.reference_date) over (
            partition by m.investor_type_code, cal.trading_month
            order by m.reference_date
        ) as prev_mtd_reference_date,
        lag(m.mtd_purchases_k_brl) over (
            partition by m.investor_type_code, cal.trading_month
            order by m.reference_date
        ) as prev_mtd_purchases_k_brl,
        lag(m.mtd_sales_k_brl) over (
            partition by m.investor_type_code, cal.trading_month
            order by m.reference_date
        ) as prev_mtd_sales_k_brl
    from mtd_flow as m
    inner join trading_calendar as cal
        on m.reference_date = cal.trading_date
),

deaccumulated as (
    select
        trading_date,
        trading_month,
        trading_year,
        publication_date,
        investor_type_code,
        investor_type_raw,
        case
            when is_first_trading_day_of_month then 'month_start_exact'
            when prev_mtd_reference_date = prev_trading_date then 'mtd_diff_exact'
            else 'missing_prior_trading_day'
        end as daily_derivation_method,
        case
            when is_first_trading_day_of_month then mtd_purchases_k_brl
            when prev_mtd_reference_date = prev_trading_date
                then mtd_purchases_k_brl - prev_mtd_purchases_k_brl
            else null
        end as daily_purchases_k_brl,
        case
            when is_first_trading_day_of_month then mtd_sales_k_brl
            when prev_mtd_reference_date = prev_trading_date
                then mtd_sales_k_brl - prev_mtd_sales_k_brl
            else null
        end as daily_sales_k_brl,
        mtd_purchases_k_brl,
        mtd_sales_k_brl,
        mtd_net_flow_k_brl,
        mtd_net_flow_bi_brl,
        purchase_share_pct,
        sale_share_pct,
        _source_system
    from joined
)

select
    cast(trading_date as varchar) || '_' || investor_type_code as investor_flow_daily_sk,
    trading_date,
    trading_month,
    trading_year,
    publication_date,
    investor_type_code,
    investor_type_raw,
    daily_derivation_method,
    daily_purchases_k_brl,
    daily_sales_k_brl,
    (daily_purchases_k_brl - daily_sales_k_brl) as daily_net_flow_k_brl,
    round((daily_purchases_k_brl - daily_sales_k_brl) / 1000000.0, 6) as daily_net_flow_bi_brl,
    mtd_purchases_k_brl,
    mtd_sales_k_brl,
    mtd_net_flow_k_brl,
    mtd_net_flow_bi_brl,
    purchase_share_pct,
    sale_share_pct,
    _source_system
from deaccumulated
order by trading_date, investor_type_code
