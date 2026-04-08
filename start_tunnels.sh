#!/bin/bash

# 1. Lancer ngrok pour le front (en arrière-plan)
ngrok http 3000 --domain=wrongfully-grizzled-janina.ngrok-free.dev > /dev/null &
NGROK_PID=$!
echo "✅ Ngrok (Front) lancé sur port 3000"

# 2. Lancer Serveo pour le back
echo "⏳ Lancement de Serveo (Back) sur port 8000..."
ssh -R 80:localhost:8000 serveo.net

echo "Quand vous avez terminé, appuyez sur Ctrl+C pour arrêter les tunnels et kill $NGROK_PID."
