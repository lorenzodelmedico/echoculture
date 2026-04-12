#!/bin/bash
echo "🚀 Backend: https://echoculture.serveousercontent.com"
while true; do
  ssh -o ServerAliveInterval=60 -o ServerAliveCountMax=3 -R echoculture:80:localhost:8000 serveo.net
  echo "⚠️ Serveo déconnecté, reconnexion..."
  sleep 5
done
