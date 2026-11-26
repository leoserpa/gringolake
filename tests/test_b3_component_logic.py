"""Unit tests for B3MarketDataComponent helper rules (year finalization, lookback, timezone)."""

from datetime import date

from gringolake.components.b3_market_data_component import (
    FINALIZED_MARKER_NAME,
    b3_today,
    resolve_lookback_days,
    should_skip_cached_year,
)


def test_b3_today_returns_date():
    assert isinstance(b3_today(), date)


def test_resolve_lookback_days_preserves_explicit_zero():
    assert resolve_lookback_days(0, 35) == 0
    assert resolve_lookback_days(5, 35) == 5
    assert resolve_lookback_days(None, 35) == 35


def test_should_skip_cached_year_requires_finalized_marker_after_rollover(tmp_path):
    part = tmp_path / "year=2026" / "part-0.parquet"
    part.parent.mkdir(parents=True)
    part.write_bytes(b"parquet")

    # Current year is never skipped
    assert not should_skip_cached_year(
        year=2026, current_year=2026, partition_file=part, force_refresh_past_years=False
    )

    # After rollover to 2027, an unfinalized 2026 cache MUST NOT be skipped
    assert not should_skip_cached_year(
        year=2026, current_year=2027, partition_file=part, force_refresh_past_years=False
    )

    # Once finalized in 2027, 2026 can be skipped safely
    (part.parent / FINALIZED_MARKER_NAME).write_text("{}", encoding="utf-8")
    assert should_skip_cached_year(
        year=2026, current_year=2027, partition_file=part, force_refresh_past_years=False
    )

    # Explicit force refresh still overrides the finalized shortcut
    assert not should_skip_cached_year(
        year=2026, current_year=2027, partition_file=part, force_refresh_past_years=True
    )
