#!/bin/bash

# 1. Serveo pour Airflow webserver (background, port 8080)
(while true; do
  ssh -o ServerAliveInterval=60 -o ServerAliveCountMax=3 \
    -R echoculture-airflow-lorenzo:80:localhost:8080 serveo.net
  echo "⚠️  Serveo Airflow déconnecté, reconnexion..."
  sleep 5
done) &
echo "✈️  Airflow: https://echoculture-airflow-lorenzo.serveo.net"

# 2. Serveo pour le Back (foreground, Auto-reconnect + URL fixe)
echo "🚀 Backend: https://echoculture-lorenzo-2026.serveo.net"
while true; do
  ssh -o ServerAliveInterval=60 -o ServerAliveCountMax=3 -R echoculture:80:localhost:8000 serveo.net
  echo "⚠️ Serveo déconnecté, tentative de reconquête de l'URL..."
  sleep 5
done
