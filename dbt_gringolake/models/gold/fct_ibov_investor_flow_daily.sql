with daily_flow as (
    select
        trading_date,
        trading_month,
        trading_year,
        publication_date,
        investor_type_code,
        daily_derivation_method,
        daily_purchases_k_brl,
        daily_sales_k_brl,
        daily_net_flow_k_brl,
        daily_net_flow_bi_brl,
        mtd_purchases_k_brl,
        mtd_sales_k_brl,
        mtd_net_flow_k_brl,
        mtd_net_flow_bi_brl,
        purchase_share_pct,
        sale_share_pct
    from {{ ref('int_b3_investor_flow_daily') }}
    where daily_net_flow_k_brl is not null
),

ibov_base as (
    select
        trading_date,
        ibov_close,
        ibov_return_1d_pct,
        max(ibov_close) over (
            order by trading_date
            rows between {{ var('local_extrema_window_days', 10) }} preceding
                     and {{ var('local_extrema_window_days', 10) }} following
        ) as local_window_max_ibov,
        min(ibov_close) over (
            order by trading_date
            rows between {{ var('local_extrema_window_days', 10) }} preceding
                     and {{ var('local_extrema_window_days', 10) }} following
        ) as local_window_min_ibov,
        max(trading_date) over () as max_ibov_trading_date
    from {{ ref('stg_b3_ibov_daily') }}
),

ibov_annotated as (
    select
        trading_date,
        ibov_close,
        ibov_return_1d_pct,
        case
            when ibov_close = local_window_max_ibov then 'peak'
            when ibov_close = local_window_min_ibov then 'trough'
            else null
        end as ibov_local_extrema_type,
        case
            when ibov_close = local_window_max_ibov
              or ibov_close = local_window_min_ibov
              or trading_date = max_ibov_trading_date
                then cast(round(ibov_close, 0) as bigint)
            else null
        end as ibov_label_points
    from ibov_base
),

cumulative_series as (
    select
        f.trading_date,
        f.trading_month,
        f.trading_year,
        f.publication_date,
        f.investor_type_code,
        d.investor_type_name_pt,
        d.investor_type_short_pt,
        d.display_order,
        i.ibov_close,
        i.ibov_return_1d_pct,
        i.ibov_local_extrema_type,
        i.ibov_label_points,
        f.daily_derivation_method,
        f.daily_purchases_k_brl,
        f.daily_sales_k_brl,
        f.daily_net_flow_k_brl,
        f.daily_net_flow_bi_brl,
        f.mtd_net_flow_k_brl,
        f.mtd_net_flow_bi_brl,
        f.purchase_share_pct,
        f.sale_share_pct,
        sum(f.daily_net_flow_k_brl) over (
            partition by f.investor_type_code
            order by f.trading_date
            rows between unbounded preceding and current row
        ) as cum_net_flow_k_brl,
        sum(f.daily_net_flow_k_brl) over (
            partition by f.investor_type_code, f.trading_year
            order by f.trading_date
            rows between unbounded preceding and current row
        ) as cum_net_flow_ytd_k_brl
    from daily_flow as f
    inner join ibov_annotated as i
        on f.trading_date = i.trading_date
    inner join {{ ref('dim_investor_type') }} as d
        on f.investor_type_code = d.investor_type_code
),

moving_averages as (
    select
        *,
        round(cum_net_flow_k_brl / 1000000.0, 6) as cum_net_flow_bi_brl,
        round(cum_net_flow_ytd_k_brl / 1000000.0, 6) as cum_net_flow_ytd_bi_brl,
        avg(cum_net_flow_k_brl) over (
            partition by investor_type_code
            order by trading_date
            rows between 20 preceding and current row
        ) as raw_cum_net_flow_ma21_k_brl,
        count(*) over (
            partition by investor_type_code
            order by trading_date
            rows between 20 preceding and current row
        ) as ma21_window_obs_count
    from cumulative_series
)

select
    cast(trading_date as varchar) || '_' || investor_type_code as fact_ibov_flow_sk,
    trading_date,
    trading_month,
    trading_year,
    publication_date,
    investor_type_code,
    investor_type_name_pt,
    investor_type_short_pt,
    display_order,
    ibov_close,
    ibov_return_1d_pct,
    ibov_local_extrema_type,
    ibov_label_points,
    daily_derivation_method,
    daily_purchases_k_brl,
    daily_sales_k_brl,
    daily_net_flow_k_brl,
    daily_net_flow_bi_brl,
    mtd_net_flow_k_brl,
    mtd_net_flow_bi_brl,
    purchase_share_pct,
    sale_share_pct,
    cum_net_flow_k_brl,
    cum_net_flow_bi_brl,
    cum_net_flow_ytd_bi_brl,
    -- ADR-006: strict 21-trading-day SMA; emit NULL during warm-up (< 21 sessions)
    -- so partial expanding means never generate fabricated crossover signals.
    case
        when ma21_window_obs_count = 21 then round(raw_cum_net_flow_ma21_k_brl, 4)
        else null
    end as cum_net_flow_ma21_k_brl,
    case
        when ma21_window_obs_count = 21 then round(raw_cum_net_flow_ma21_k_brl / 1000000.0, 6)
        else null
    end as cum_net_flow_ma21_bi_brl,
    case
        when ma21_window_obs_count = 21
            then round((cum_net_flow_k_brl - raw_cum_net_flow_ma21_k_brl) / 1000000.0, 6)
        else null
    end as flow_vs_ma21_spread_bi_brl,
    case
        when ma21_window_obs_count < 21 then 'em_formacao'
        when cum_net_flow_k_brl >= raw_cum_net_flow_ma21_k_brl then 'acima_mm21'
        else 'abaixo_mm21'
    end as flow_vs_ma21_signal,
    cast(ma21_window_obs_count as integer) as ma21_window_obs_count,
    (ma21_window_obs_count = 21) as has_full_ma21_window
from moving_averages
order by trading_date, display_order
