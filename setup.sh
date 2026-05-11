#!/bin/bash
# ============================================================
# SynkOS — first-time bootstrap
# ============================================================
# Run from a fresh clone, after `cp .env.example .env` and filling in values.
# Idempotent: safe to re-run.
# ============================================================

set -e

if [[ ! -f .env ]]; then
    echo "❌ .env not found. Run: cp .env.example .env  and fill in values."
    exit 1
fi

# Ensure the logs dir exists with permissions Airflow can write to
mkdir -p logs
chmod 777 logs

# Build images and bring everything up (cloudflared stays off — opt in with --profile cloudflare)
echo "🐳 Building and starting services..."
docker compose up -d --build

echo "⏳ Waiting 15s for Postgres / Mongo / Airflow to settle..."
sleep 15

echo "✅ Services up. Useful URLs:"
echo "   • App           http://localhost:3000"
echo "   • Airflow       http://localhost:8080  (admin / admin)"
echo "   • Adminer (PG)  http://localhost:8082"
echo "   • Mongo Express http://localhost:8081"
echo
echo "📥 Trigger the first scrape from the Airflow UI (or):"
echo "   docker exec echoculture-airflow-scheduler-1 airflow dags trigger scraper_bdxc_mongodb_to_pg"
