#!/usr/bin/env bash
# Detecta drift entre arquivos de código e sua documentação/ADRs usando o histórico do Git.
# Baseado na skill documentation-and-adrs: quando o histórico Git não existe, é raso (shallow),
# possui alterações locais não commitadas ou ordem ancestral indefinida, reporta explicitamente
# "can't tell" em vez de declarar "current".

set -euo pipefail

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "can't tell: diretório não é um repositório Git (sem histórico de commits para comparar)."
  exit 0
fi

if [ "$(git rev-parse --is-shallow-repository 2>/dev/null || echo false)" = "true" ]; then
  echo "can't tell: repositório em clone shallow (histórico insuficiente para determinar ordem de commits)."
  exit 0
fi

check_pair() {
  local code_path="$1"
  local doc_path="$2"

  if [ ! -e "$code_path" ] || [ ! -e "$doc_path" ]; then
    echo "can't tell: caminho ausente ($code_path <-> $doc_path)"
    return
  fi

  if [ -n "$(git status --porcelain -- "$code_path" "$doc_path" 2>/dev/null || true)" ]; then
    echo "can't tell (uncommitted local changes): $doc_path <-> $code_path"
    return
  fi

  local code_hash doc_hash
  code_hash=$(git log -1 --format=%H -- "$code_path" 2>/dev/null || true)
  doc_hash=$(git log -1 --format=%H -- "$doc_path" 2>/dev/null || true)

  if [ -z "$code_hash" ] || [ -z "$doc_hash" ]; then
    echo "can't tell: sem commit registrado para $code_path ou $doc_path"
    return
  fi

  if [ "$code_hash" = "$doc_hash" ]; then
    echo "current (changed together): $doc_path <-> $code_path"
  elif git merge-base --is-ancestor "$doc_hash" "$code_hash" 2>/dev/null; then
    echo "STALE (code changed after doc): $doc_path <-> $code_path"
  elif git merge-base --is-ancestor "$code_hash" "$doc_hash" 2>/dev/null; then
    echo "current (doc changed after code): $doc_path <-> $code_path"
  else
    echo "can't tell (unordered history): $doc_path <-> $code_path"
  fi
}

check_pair "src/gringolake/clients/b3_client.py" "docs/decisions/002-official-b3-data-sources-only.md"
check_pair "dbt_gringolake/models/silver/int_b3_investor_flow_daily.sql" "docs/decisions/003-mtd-deaccumulation-using-ibov-calendar.md"
check_pair "src/gringolake/definitions.py" "docs/decisions/004-dual-storage-duckdb-and-zstd-parquet.md"
check_pair "dbt_gringolake/macros/export_parquet.sql" "docs/decisions/004-dual-storage-duckdb-and-zstd-parquet.md"
check_pair "dbt_gringolake/tests/assert_b3_daily_flow_zero_sum.sql" "docs/decisions/005-multi-layer-data-quality-and-zero-sum-invariant.md"
check_pair "dbt_gringolake/tests/assert_ma21_window_integrity.sql" "docs/decisions/006-strict-ma21-full-window-and-unified-brl-billions.md"
check_pair "dbt_gringolake/models/gold/fct_ibov_investor_flow_daily.sql" "docs/data-dictionary.md"
check_pair "src/gringolake/components/b3_market_data_component.py" "AGENTS.md"
