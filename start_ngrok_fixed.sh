#!/bin/bash

# Start ngrok with User-Agent header to bypass browser warning
ngrok http 3000 \
  --domain wrongfully-grizzled-janina.ngrok-free.dev \
  --host-header=rewrite \
  --request-header-add="x-custom-user-agent: EchoCulture/1.0"
