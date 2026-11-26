with pf_ranked as (
    select
        trading_date,
        ibov_close,
        ibov_return_1d_pct,
        ibov_local_extrema_type,
        ibov_label_points,
        daily_net_flow_k_brl,
        daily_net_flow_bi_brl,
        row_number() over (order by trading_date desc) as recency_rank
    from {{ ref('fct_ibov_investor_flow_daily') }}
    where investor_type_code = 'pessoa_fisica'
),

short_term_window as (
    select
        trading_date,
        ibov_close,
        ibov_return_1d_pct,
        ibov_local_extrema_type,
        ibov_label_points,
        daily_net_flow_k_brl,
        daily_net_flow_bi_brl,
        sum(daily_net_flow_k_brl) over (
            order by trading_date
            rows between unbounded preceding and current row
        ) as pf_cum_short_term_k_brl
    from pf_ranked
    where recency_rank <= {{ var('short_term_trading_days', 160) }}
),

with_ma21 as (
    select
        trading_date,
        ibov_close,
        ibov_return_1d_pct,
        ibov_local_extrema_type,
        ibov_label_points,
        daily_net_flow_k_brl,
        daily_net_flow_bi_brl,
        pf_cum_short_term_k_brl,
        round(pf_cum_short_term_k_brl / 1000000.0, 6) as pf_cum_short_term_bi_brl,
        avg(pf_cum_short_term_k_brl) over (
            order by trading_date
            rows between 20 preceding and current row
        ) as pf_cum_short_term_ma21_k_brl,
        count(*) over (
            order by trading_date
            rows between 20 preceding and current row
        ) as ma21_window_obs_count
    from short_term_window
)

select
    trading_date,
    ibov_close,
    ibov_return_1d_pct,
    ibov_local_extrema_type,
    ibov_label_points,
    daily_net_flow_k_brl,
    daily_net_flow_bi_brl,
    pf_cum_short_term_k_brl,
    pf_cum_short_term_bi_brl,
    round(pf_cum_short_term_ma21_k_brl, 4) as pf_cum_short_term_ma21_k_brl,
    round(pf_cum_short_term_ma21_k_brl / 1000000.0, 6) as pf_cum_short_term_ma21_bi_brl,
    (pf_cum_short_term_k_brl < pf_cum_short_term_ma21_k_brl) as is_pf_below_ma21,
    (ma21_window_obs_count = 21) as has_full_ma21_window
from with_ma21
order by trading_date
