#!/bin/bash
echo "✈️  Airflow: https://echoculture-airflow-lorenzo.serveo.net"
while true; do
  ssh -o ServerAliveInterval=60 -o ServerAliveCountMax=3 -R echoculture-airflow-lorenzo:80:localhost:8080 serveo.net
  echo "⚠️  Serveo Airflow déconnecté, reconnexion..."
  sleep 5
done
