#!/bin/bash

# Ativa o ambiente virtual
source .venv/bin/activate

# Exporta as variáveis de ambiente
export SSL_CERT_FILE="$PWD/.venv/lib/python3.12/site-packages/certifi/cacert.pem"
export REQUESTS_CA_BUNDLE="$PWD/.venv/lib/python3.12/site-packages/certifi/cacert.pem"

# Carrega as outras variáveis do .env
set -a
source .env
set +a

# Inicia o servidor
python chat/chat_server.py
