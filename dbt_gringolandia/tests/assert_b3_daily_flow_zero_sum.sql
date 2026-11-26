-- Invariante contábil de mercado (jogo de soma zero):
-- Na B3, cada R$ 1 comprado por uma categoria de investidor é vendido por outra.
-- Portanto, a soma do saldo líquido diário de todas as 5 categorias em cada pregão
-- deve fechar em zero (tolerância de ±20 R$ mil devido a arredondamentos por categoria no BDI).

with daily_balance as (
    select
        trading_date,
        count(distinct investor_type_code) as investor_categories_count,
        sum(daily_net_flow_k_brl) as total_market_net_flow_k_brl
    from {{ ref('fct_ibov_investor_flow_daily') }}
    group by trading_date
)

select
    trading_date,
    investor_categories_count,
    total_market_net_flow_k_brl
from daily_balance
where investor_categories_count != 5
   or abs(total_market_net_flow_k_brl) > 20.0
