#!/usr/bin/env bash
# Trigger all data-ingestion DAGs and wait for them to finish.
# Run this after a fresh deploy to populate the DB from scratch.
#
# Usage:  ./populate_db.sh
#
# Requirements: the compose stack must already be up (docker compose up -d).

set -euo pipefail

SCHEDULER="echoculture-airflow-scheduler-1"
DAGS=(
    "scraper_bdxc_mongodb_to_pg"
    "scraper_bdxc_spectacles"
    "scraper_bdxc_expositions"
    "scraper_ecrantotal_films"
    "scraper_bdxc_prices"
)

trigger() {
    docker exec "$SCHEDULER" airflow dags trigger "$1" > /dev/null 2>&1
}

wait_for_dag() {
    local dag="$1"
    local max_wait=900  # 15 min timeout per DAG
    local elapsed=0
    while true; do
        state=$(docker exec "$SCHEDULER" airflow dags state "$dag" "$(date +%Y-%m-%d)" 2>/dev/null | tail -1 || echo "unknown")
        case "$state" in
            success) return 0 ;;
            failed)  echo "  [FAIL] $dag"; return 1 ;;
        esac
        if [ "$elapsed" -ge "$max_wait" ]; then
            echo "  [TIMEOUT] $dag did not finish within ${max_wait}s"
            return 1
        fi
        sleep 15
        elapsed=$((elapsed + 15))
        echo "  ... $dag ($state, ${elapsed}s)"
    done
}

echo "==> Triggering all ingestion DAGs"
for dag in "${DAGS[@]}"; do
    echo "  Triggering $dag"
    trigger "$dag"
done

echo ""
echo "==> Waiting for DAGs to complete (this can take 10-30 min on first run)"
all_ok=true
for dag in "${DAGS[@]}"; do
    echo "Waiting: $dag"
    if ! wait_for_dag "$dag"; then
        all_ok=false
    fi
    echo "  Done: $dag"
done

echo ""
if $all_ok; then
    echo "==> All DAGs finished successfully. DB is populated."
else
    echo "==> Some DAGs failed. Check Airflow UI at http://localhost:8080"
fi
