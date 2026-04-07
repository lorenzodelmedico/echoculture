#!/bin/bash

echo "🚀 Démarrage du setup complet d'EchoCulture..."

# 1. Nettoyage radical (On repart sur des bases saines)
echo "🧹 Nettoyage des anciens conteneurs et volumes..."
docker compose down -v

# 2. Suppression des logs locaux pour éviter les erreurs de permissions
rm -rf ./logs
mkdir logs

# 3. Lancement des services Docker (Postgres, Mongo, Airflow)
echo "🐳 Lancement de Docker (Build & Up)..."
docker compose up -d --build

echo "⏳ Attente du démarrage des bases de données (15s)..."
sleep 15

# 4. Peuplement du Bronze (Via ton script local Poetry)
echo "📥 Récupération des données Bronze (Scraping)..."

poetry run python -m scrapers.archipop_bronze

echo "✅ Setup terminé !"
echo "👉 Tu peux maintenant lancer le test Silver avec :"
echo "docker exec -it echoculture-airflow-scheduler-1 airflow tasks test archipop_pipeline llm_structuration 2026-04-06"
