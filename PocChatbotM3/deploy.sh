#!/usr/bin/env bash
set -euo pipefail

# --- Paramètres ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Image ACR par défaut (tu peux override avec: IMAGE_NAME=... ./deploy.sh)
IMAGE_NAME="${IMAGE_NAME:-acrchatbotm3.azurecr.io/chatbot-poc:vtest3}"

# Nom du conteneur et ports (8503 -> 8501 comme dans ta commande)
CONTAINER_NAME="${CONTAINER_NAME:-chatbot-test}"
HOST_PORT="${HOST_PORT:-8501}"
CONTAINER_PORT=8501

# Racine applicative attendue par l'image
APP_ROOT="${APP_ROOT:-/app/PocChatbotM3}"

# Dossiers hôte (créés si absents)
RUNTIME_DIR_HOST="${RUNTIME_DIR_HOST:-$SCRIPT_DIR/runtime_data}"
VECTOR_DB_HOST="${VECTOR_DB_HOST:-$SCRIPT_DIR/vector_db}"
INPUTS_OXY_HOST="${INPUTS_OXY_HOST:-$SCRIPT_DIR/inputs/Oxypharm}"

# Active l’étiquette SELinux :Z si besoin (true/false)
USE_SELINUX_LABEL="${USE_SELINUX_LABEL:-false}"
SELINUX_FLAG=""
if [[ "${USE_SELINUX_LABEL}" == "true" ]]; then
  SELINUX_FLAG=":Z"
fi

# --- Préchecks ---
if ! command -v docker >/dev/null 2>&1; then
  echo "docker command not found. Install Docker before running this script." >&2
  exit 1
fi

if [[ ! -f "$SCRIPT_DIR/.env" ]]; then
  echo ".env file missing in $SCRIPT_DIR. Create it before deploying." >&2
  exit 1
fi

echo "[deploy] Preparing runtime directories..."
mkdir -p \
  "$RUNTIME_DIR_HOST/database" \
  "$VECTOR_DB_HOST" \
  "$INPUTS_OXY_HOST"

# --- Pull de l'image distante (ACR) ---
echo "[deploy] Pulling image $IMAGE_NAME..."
docker pull "$IMAGE_NAME"

# --- Stop & remove précédent conteneur si présent ---
if docker ps -a --format '{{.Names}}' | grep -Fxq "$CONTAINER_NAME"; then
  echo "[deploy] Stopping previous container $CONTAINER_NAME..."
  docker rm -f "$CONTAINER_NAME" >/dev/null
fi

# --- Lancement ---
echo "[deploy] Launching container on port $HOST_PORT..."
docker run -d \
  --name "$CONTAINER_NAME" \
  --restart unless-stopped \
  -p "${HOST_PORT}:${CONTAINER_PORT}" \
  --env-file "$SCRIPT_DIR/.env" \
  -e CHATBOT_RUNTIME_DIR="${APP_ROOT}/runtime_data" \
  -e RAG_STORE=faiss \
  -e FAISS_INDEX_DIR="${APP_ROOT}/vector_db" \
  -e SQLALCHEMY_URL="sqlite:////${APP_ROOT}/runtime_data/database/interactions.db" \
  -v "${VECTOR_DB_HOST}:${APP_ROOT}/runtime_data/vector_db${SELINUX_FLAG}" \
  -v "${RUNTIME_DIR_HOST}/database:${APP_ROOT}/runtime_data/database${SELINUX_FLAG}" \
  -v "${INPUTS_OXY_HOST}:/app/inputs/Oxypharm${SELINUX_FLAG}" \
  "$IMAGE_NAME"

echo "[deploy] Container $CONTAINER_NAME is running on http://localhost:${HOST_PORT}"
