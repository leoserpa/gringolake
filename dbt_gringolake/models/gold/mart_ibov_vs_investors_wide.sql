with fact_flow as (
    select
        trading_date,
        trading_month,
        trading_year,
        ibov_close,
        ibov_return_1d_pct,
        ibov_local_extrema_type,
        ibov_label_points,
        investor_type_code,
        daily_net_flow_bi_brl,
        cum_net_flow_bi_brl,
        cum_net_flow_ma21_bi_brl,
        cum_net_flow_k_brl,
        cum_net_flow_ma21_k_brl,
        ma21_window_obs_count,
        has_full_ma21_window
    from {{ ref('fct_ibov_investor_flow_daily') }}
)

select
    trading_date,
    trading_month,
    trading_year,
    max(ibov_close) as ibov_close,
    max(ibov_return_1d_pct) as ibov_return_1d_pct,
    max(ibov_local_extrema_type) as ibov_local_extrema_type,
    max(ibov_label_points) as ibov_label_points,
    min(ma21_window_obs_count) as ma21_window_obs_count,
    bool_and(has_full_ma21_window) as has_full_ma21_window,

    -- Investidor Estrangeiro (ESTRANG)
    max(case when investor_type_code = 'estrangeiro' then daily_net_flow_bi_brl end) as estrang_daily_bi_brl,
    max(case when investor_type_code = 'estrangeiro' then cum_net_flow_bi_brl end) as estrang_cum_bi_brl,
    max(case when investor_type_code = 'estrangeiro' then cum_net_flow_ma21_bi_brl end) as estrang_cum_ma21_bi_brl,

    -- Institucional (INSTIT.)
    max(case when investor_type_code = 'institucional' then daily_net_flow_bi_brl end) as instit_daily_bi_brl,
    max(case when investor_type_code = 'institucional' then cum_net_flow_bi_brl end) as instit_cum_bi_brl,
    max(case when investor_type_code = 'institucional' then cum_net_flow_ma21_bi_brl end) as instit_cum_ma21_bi_brl,

    -- Pessoa Física (P.F.)
    max(case when investor_type_code = 'pessoa_fisica' then daily_net_flow_bi_brl end) as pf_daily_bi_brl,
    max(case when investor_type_code = 'pessoa_fisica' then cum_net_flow_bi_brl end) as pf_cum_bi_brl,
    max(case when investor_type_code = 'pessoa_fisica' then cum_net_flow_ma21_bi_brl end) as pf_cum_ma21_bi_brl,

    -- Instituições Financeiras (INST. FIN.)
    max(case when investor_type_code = 'instituicoes_financeiras' then daily_net_flow_bi_brl end) as inst_fin_daily_bi_brl,
    max(case when investor_type_code = 'instituicoes_financeiras' then cum_net_flow_bi_brl end) as inst_fin_cum_bi_brl,
    max(case when investor_type_code = 'instituicoes_financeiras' then cum_net_flow_ma21_bi_brl end) as inst_fin_cum_ma21_bi_brl,

    -- Outros (OUTROS)
    max(case when investor_type_code = 'outros' then daily_net_flow_bi_brl end) as outros_daily_bi_brl,
    max(case when investor_type_code = 'outros' then cum_net_flow_bi_brl end) as outros_cum_bi_brl,
    max(case when investor_type_code = 'outros' then cum_net_flow_ma21_bi_brl end) as outros_cum_ma21_bi_brl,

    -- R$ mil (unidade original B3 / cabeçalho dos gráficos)
    max(case when investor_type_code = 'estrangeiro' then cum_net_flow_k_brl end) as estrang_cum_k_brl,
    max(case when investor_type_code = 'institucional' then cum_net_flow_k_brl end) as instit_cum_k_brl,
    max(case when investor_type_code = 'pessoa_fisica' then cum_net_flow_k_brl end) as pf_cum_k_brl
from fact_flow
group by
    trading_date,
    trading_month,
    trading_year
order by trading_date
