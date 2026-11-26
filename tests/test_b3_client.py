"""Unit tests for the official B3 API client and parsers."""

from datetime import date
from unittest.mock import MagicMock

import pytest

from gringolandia.clients.b3_client import (
    B3Client,
    parse_b3_reference_date,
    parse_br_number,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("100.774,57", 100774.57),
        ("130.776,00", 130776.0),
        ("0,00", 0.0),
        (" 12.345,67 ", 12345.67),
        (155354933, 155354933.0),
        (12.78, 12.78),
        ("", None),
        ("   ", None),
        (None, None),
    ],
)
def test_parse_br_number(raw, expected):
    assert parse_br_number(raw) == expected


def test_parse_b3_reference_date_from_official_note():
    note = (
        "Contribuição de diferentes perfis de investidores no volume total de negociações "
        "realizadas na B3.\r\nDados acumulados do início do mês até o dia 23/11/2026."
    )
    assert parse_b3_reference_date(note) == date(2026, 11, 23)
    assert parse_b3_reference_date("") is None
    assert parse_b3_reference_date(None) is None
    assert parse_b3_reference_date("Sem data informada") is None


def test_fetch_ibov_daily_for_year_parses_grid_correctly():
    fake_payload = {
        "results": [
            {
                "day": 1,
                "rateValue1": None,
                "rateValue2": "117.517,57",
                "rateValue12": "100.774,57",
            },
            {
                "day": 2,
                "rateValue1": None,
                "rateValue2": "118.234,00",
                "rateValue12": None,
            },
        ]
    }
    mock_resp = MagicMock()
    mock_resp.content = b'{"results": []}'
    mock_resp.json.return_value = fake_payload

    client = B3Client()
    client._request = MagicMock(return_value=mock_resp)

    res = client.fetch_ibov_daily_for_year(2021)
    assert res.year == 2021
    assert len(res.records) == 3
    assert [r["trading_date"] for r in res.records] == [
        date(2021, 2, 1),
        date(2021, 2, 2),
        date(2021, 12, 1),
    ]
    assert res.records[2]["ibov_close"] == pytest.approx(100774.57)
    client.close()


def test_fetch_investor_flow_mtd_extracts_reference_date_and_rows():
    fake_payload = {
        "table": {
            "limitDate": "D-21",
            "texts": [
                {
                    "textPt": (
                        "Contribuição de diferentes perfis.\r\n"
                        "Dados acumulados do início do mês até o dia 03/11/2026."
                    )
                }
            ],
            "values": [
                ["Investidor Estrangeiro", 30000000, 31.0, 29000000, 30.0, None],
                ["Investidores Individuais", 5042988, 5.92, 4225868, 4.96, None],
            ],
        }
    }
    mock_resp = MagicMock()
    mock_resp.content = b'{"table": {}}'
    mock_resp.json.return_value = fake_payload

    client = B3Client()
    client._request = MagicMock(return_value=mock_resp)

    res = client.fetch_investor_flow_mtd_for_date(date(2026, 11, 5))
    assert res.publication_date == date(2026, 11, 5)
    assert res.reference_date == date(2026, 11, 3)
    assert len(res.records) == 2
    assert res.records[1]["investor_type_raw"] == "Investidores Individuais"
    assert res.records[1]["mtd_purchases_k_brl"] == pytest.approx(5042988.0)
    assert res.records[1]["mtd_sales_k_brl"] == pytest.approx(4225868.0)
    client.close()
