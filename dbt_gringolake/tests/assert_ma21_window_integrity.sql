-- Garante rigor estatístico da MM21 (ADR-006):
-- 1) Com menos de 21 pregões (has_full_ma21_window = false), a MM21 e o spread DEVEM ser NULL,
--    o sinal DEVE ser 'em_formacao' e o alerta is_pf_below_ma21 DEVE ser false.
-- 2) Com 21 pregões completos (has_full_ma21_window = true), a MM21 e o spread NÃO podem ser NULL
--    e o sinal DEVE ser 'acima_mm21' ou 'abaixo_mm21'.

with fact_violations as (
    select
        'fct_ibov_investor_flow_daily' as model_name,
        cast(trading_date as varchar) as trading_date,
        investor_type_code,
        ma21_window_obs_count,
        has_full_ma21_window,
        flow_vs_ma21_signal
    from {{ ref('fct_ibov_investor_flow_daily') }}
    where (
        not has_full_ma21_window
        and (
            ma21_window_obs_count >= 21
            or cum_net_flow_ma21_k_brl is not null
            or cum_net_flow_ma21_bi_brl is not null
            or flow_vs_ma21_spread_bi_brl is not null
            or flow_vs_ma21_signal != 'em_formacao'
        )
    )
    or (
        has_full_ma21_window
        and (
            ma21_window_obs_count != 21
            or cum_net_flow_ma21_k_brl is null
            or cum_net_flow_ma21_bi_brl is null
            or flow_vs_ma21_spread_bi_brl is null
            or flow_vs_ma21_signal not in ('acima_mm21', 'abaixo_mm21')
        )
    )
),

short_term_violations as (
    select
        'mart_ibov_vs_pf_short_term' as model_name,
        cast(trading_date as varchar) as trading_date,
        'pessoa_fisica' as investor_type_code,
        ma21_window_obs_count,
        has_full_ma21_window,
        case when is_pf_below_ma21 then 'below' else 'not_below' end as flow_vs_ma21_signal
    from {{ ref('mart_ibov_vs_pf_short_term') }}
    where (
        not has_full_ma21_window
        and (
            ma21_window_obs_count >= 21
            or pf_cum_short_term_ma21_k_brl is not null
            or pf_cum_short_term_ma21_bi_brl is not null
            or is_pf_below_ma21
        )
    )
    or (
        has_full_ma21_window
        and (
            ma21_window_obs_count != 21
            or pf_cum_short_term_ma21_k_brl is null
            or pf_cum_short_term_ma21_bi_brl is null
        )
    )
)

select * from fact_violations
union all
select * from short_term_violations
