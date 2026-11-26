"""Official B3 public market data client.

Sources (100% official B3):
1. IBOVESPA daily official closing index:
   GET https://sistemaswebb3-listados.b3.com.br/indexStatisticsProxy/IndexCall/GetPortfolioDay/{b64}
2. Participação dos Investidores (Boletim Diário de Informações - BDI):
   POST https://arquivos.b3.com.br/bdi/table/SharesInvesVolum/{YYYY-MM-DD}/{YYYY-MM-DD}/1/50
"""

from __future__ import annotations

import base64
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any, Self

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

B3_IBOV_BASE_URL = (
    "https://sistemaswebb3-listados.b3.com.br/indexStatisticsProxy/IndexCall/GetPortfolioDay"
)
B3_BDI_INVESTOR_FLOW_URL = "https://arquivos.b3.com.br/bdi/table/SharesInvesVolum"

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8",
}

_DATE_BR_RE = re.compile(r"(\d{2})/(\d{2})/(\d{4})")


class B3TransientError(RuntimeError):
    """Retryable transient error returned by B3 endpoints."""


@dataclass(frozen=True)
class B3IbovFetchResult:
    year: int
    source_url: str
    payload_hash: str
    raw_payload: dict[str, Any]
    records: list[dict[str, Any]]


@dataclass(frozen=True)
class B3InvestorFlowFetchResult:
    publication_date: date
    reference_date: date | None
    source_url: str
    source_note_pt: str
    payload_hash: str
    raw_payload: dict[str, Any]
    records: list[dict[str, Any]]


def parse_br_number(raw: str | float | None) -> float | None:
    """Parse Brazilian decimal string (e.g., '100.774,57') into float.

    Args:
        raw: Brazilian-formatted string, numeric value, or None.

    Returns:
        Parsed floating-point value, or None when input is blank/None.

    Raises:
        ValueError: If a non-empty string cannot be converted to float.
    """
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    cleaned = raw.strip()
    if not cleaned:
        return None
    normalized = cleaned.replace(".", "").replace(",", ".")
    return float(normalized)


def parse_b3_reference_date(note_pt: str | None) -> date | None:
    """Extract the true reference trading date from B3 BDI's official Portuguese note.

    B3 BDI `SharesInvesVolum` publishes with a D+2 lag; `publication_date` is NOT
    the trading date of the figures. See ADR-003 for de-accumulation rules.

    Args:
        note_pt: Official `table.texts[0].textPt` string from B3 BDI response.

    Returns:
        Reference `date` parsed from `DD/MM/YYYY`, or None if absent.
    """
    if not note_pt:
        return None
    match = _DATE_BR_RE.search(note_pt)
    if not match:
        return None
    day_s, month_s, year_s = match.groups()
    return date(int(year_s), int(month_s), int(day_s))


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


class B3Client:
    """HTTP client for official B3 market data APIs with exponential backoff."""

    def __init__(self, timeout_seconds: float = 20.0) -> None:
        self._client = httpx.Client(
            headers=DEFAULT_HEADERS,
            timeout=httpx.Timeout(timeout_seconds),
            follow_redirects=True,
        )

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    @retry(
        reraise=True,
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=0.8, min=0.8, max=8.0),
        retry=retry_if_exception_type((httpx.TransportError, B3TransientError)),
    )
    def _request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        response = self._client.request(method, url, **kwargs)
        if response.status_code == 429 or response.status_code >= 500:
            raise B3TransientError(f"Transient B3 HTTP {response.status_code} for {url}")
        response.raise_for_status()
        return response

    def fetch_ibov_daily_for_year(self, year: int, index_code: str = "IBOV") -> B3IbovFetchResult:
        """Fetch official daily closing prices for IBOV in a given calendar year."""
        payload_dict = {"index": index_code, "language": "pt-br", "year": year}
        encoded = base64.b64encode(
            json.dumps(payload_dict, separators=(",", ":")).encode("utf-8")
        ).decode("utf-8")
        url = f"{B3_IBOV_BASE_URL}/{encoded}"

        response = self._request("GET", url)
        raw_bytes = response.content
        payload_hash = _sha256_bytes(raw_bytes)
        payload = response.json()
        ingested_at = datetime.now(UTC)

        records: list[dict[str, Any]] = []
        for row in payload.get("results") or []:
            day_num = int(row["day"])
            for month_num in range(1, 13):
                raw_val = row.get(f"rateValue{month_num}")
                parsed_val = parse_br_number(raw_val)
                if parsed_val is None:
                    continue
                trading_dt = date(year, month_num, day_num)
                records.append(
                    {
                        "trading_date": trading_dt,
                        "index_code": index_code,
                        "ibov_close_raw": str(raw_val).strip(),
                        "ibov_close": parsed_val,
                        "year": year,
                        "_source_system": "b3_index_statistics_api",
                        "_source_url": url,
                        "_payload_hash": payload_hash,
                        "_ingested_at": ingested_at,
                    }
                )

        records.sort(key=lambda r: r["trading_date"])
        return B3IbovFetchResult(
            year=year,
            source_url=url,
            payload_hash=payload_hash,
            raw_payload=payload,
            records=records,
        )

    def fetch_investor_flow_mtd_for_date(
        self, publication_date: date
    ) -> B3InvestorFlowFetchResult:
        """Fetch official B3 BDI SharesInvesVolum snapshot for a publication date.

        Note:
            B3 publishes cumulative Month-To-Date (MTD) purchase/sale values in R$ mil
            with a standard D+2 trading-day settlement lag. The true reference date is
            extracted from the official Portuguese note returned inside the API payload.
        """
        iso = publication_date.isoformat()
        url = f"{B3_BDI_INVESTOR_FLOW_URL}/{iso}/{iso}/1/50"

        response = self._request("POST", url, json={})
        raw_bytes = response.content
        payload_hash = _sha256_bytes(raw_bytes)
        payload = response.json()
        ingested_at = datetime.now(UTC)

        table = payload.get("table") or {}
        values = table.get("values") or []
        texts = table.get("texts") or []
        source_note_pt = (texts[0].get("textPt") or "").strip() if texts else ""
        reference_date = parse_b3_reference_date(source_note_pt)

        records: list[dict[str, Any]] = []
        for row in values:
            # Official BDI schema:
            # [0]: TckrSymb (Tipos de investidores)
            # [1]: Purchase (Compras R$ mil, MTD)
            # [2]: Sales (Participação % nas compras)
            # [3]: Partmil (Vendas R$ mil, MTD)
            # [4]: PartPer (Participação % nas vendas)
            if len(row) < 5 or row[0] is None:
                continue
            records.append(
                {
                    "publication_date": publication_date,
                    "reference_date": reference_date,
                    "investor_type_raw": str(row[0]).strip(),
                    "mtd_purchases_k_brl": parse_br_number(row[1]),
                    "purchase_share_pct": parse_br_number(row[2]),
                    "mtd_sales_k_brl": parse_br_number(row[3]),
                    "sale_share_pct": parse_br_number(row[4]),
                    "source_note_pt": source_note_pt,
                    "bdi_limit_date": str(table.get("limitDate") or ""),
                    "_source_system": "b3_bdi_api",
                    "_source_url": url,
                    "_payload_hash": payload_hash,
                    "_ingested_at": ingested_at,
                }
            )

        return B3InvestorFlowFetchResult(
            publication_date=publication_date,
            reference_date=reference_date,
            source_url=url,
            source_note_pt=source_note_pt,
            payload_hash=payload_hash,
            raw_payload=payload,
            records=records,
        )
