.PHONY: help check run-bronze run-dbt run-all test test-python test-dbt lint dev

help:
	@echo "GringoLake - Pipeline Medalhao B3 (Dagster + Polars + DuckDB + dbt)"
	@echo ""
	@echo "Comandos disponiveis:"
	@echo "  make check        - Valida componentes e definicoes Dagster + dbt"
	@echo "  make run-bronze   - Materializa os assets Bronze oficiais da B3"
	@echo "  make run-dbt      - Executa dbt build (Silver + Gold + unit/data tests)"
	@echo "  make run-all      - Executa todo o DAG Medalhao ponta a ponta via Dagster"
	@echo "  make test         - Roda todos os testes (pytest + dbt unit & data tests)"
	@echo "  make lint         - Roda ruff check no codigo Python"
	@echo "  make dev          - Sobe a UI web do Dagster (dg dev)"

check:
	uv run dg check defs

run-bronze:
	uv run dg launch --assets bronze/b3_ibov_daily,bronze/b3_investor_flow_mtd

run-dbt:
	cd dbt_gringolake && uv run dbt build --profiles-dir .

run-all:
	uv run dg launch --job b3_medallion_full_refresh

test-python:
	uv run pytest -v

test-dbt:
	cd dbt_gringolake && uv run dbt test --profiles-dir .

test: test-python test-dbt

lint:
	uv run ruff check src tests

dev:
	uv run dg dev
