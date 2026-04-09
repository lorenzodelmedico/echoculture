#!/bin/bash

# Ton sous-domaine Serveo choisi (ex: echoculture-api)
SUBDOMAIN="echoculture"

# 1. Ngrok pour le Front (L'URL que tu as sur ton tel)
ngrok http 3000 --domain=wrongfully-grizzled-janina.ngrok-free.dev > /dev/null &
NGROK_PID=$!
echo "✅ Frontend: https://wrongfully-grizzled-janina.ngrok-free.dev"

# 2. Serveo pour le Back (Auto-reconnect + URL fixe)
echo "🚀 Backend: https://$SUBDOMAIN.serveo.net"
while true; do
  ssh -o ServerAliveInterval=60 -o ServerAliveCountMax=3 -R echoculture-lorenzo-2026:80:localhost:8000 serveo.net
  echo "⚠️ Serveo déconnecté, tentative de reconquête de l'URL..."
  sleep 5
done
