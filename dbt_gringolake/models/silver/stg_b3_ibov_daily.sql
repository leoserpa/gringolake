with raw_ibov as (
    select
        cast(trading_date as date) as trading_date,
        cast(index_code as varchar) as index_code,
        cast(ibov_close as double) as ibov_close,
        cast(_source_system as varchar) as _source_system,
        cast(_ingested_at as timestamptz) as _ingested_at
    from {{ source('bronze', 'b3_ibov_daily') }}
    where trading_date is not null
      and ibov_close is not null
),

deduplicated as (
    select
        trading_date,
        index_code,
        ibov_close,
        _source_system,
        _ingested_at,
        row_number() over (
            partition by trading_date
            order by _ingested_at desc
        ) as rn
    from raw_ibov
),

calendar_enriched as (
    select
        trading_date,
        index_code,
        ibov_close,
        cast(date_trunc('month', trading_date) as date) as trading_month,
        cast(extract(year from trading_date) as integer) as trading_year,
        lag(trading_date) over (order by trading_date) as prev_trading_date,
        lag(ibov_close) over (order by trading_date) as prev_ibov_close,
        cast(
            row_number() over (
                partition by date_trunc('month', trading_date)
                order by trading_date
            ) as integer
        ) as trading_day_num_in_month,
        _source_system,
        _ingested_at
    from deduplicated
    where rn = 1
)

select
    trading_date,
    index_code,
    ibov_close,
    trading_month,
    trading_year,
    prev_trading_date,
    prev_ibov_close,
    round(((ibov_close / nullif(prev_ibov_close, 0.0)) - 1.0) * 100.0, 4) as ibov_return_1d_pct,
    trading_day_num_in_month,
    (trading_day_num_in_month = 1) as is_first_trading_day_of_month,
    _source_system,
    _ingested_at
from calendar_enriched
order by trading_date
