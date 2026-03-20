#!/usr/bin/env bash
set -euo pipefail

# Get the directory where the script is located
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd "$SCRIPT_DIR"

# Ensure update_repo.sh exists and is executable
if [ ! -f "./update_repo.sh" ]; then
  echo "Error: update_repo.sh not found in $SCRIPT_DIR"
  exit 1
fi
chmod +x ./update_repo.sh

# Detect current branch (defaults to main if detection fails)
CURRENT_BRANCH=$(git symbolic-ref --quiet --short HEAD || echo "main")

echo "Starting update for branch: $CURRENT_BRANCH"

# Call update_repo.sh, passing all arguments.
# It will handle adding, committing, and pushing.
./update_repo.sh --remote origin --branch "$CURRENT_BRANCH" --push "$@"

# --- INTEGRACIÓN HUGGING FACE ---
# 1. Intentar cargar el token desde .env si no está en el entorno
if [ -z "${HF_TOKEN:-}" ] && [ -f .env ]; then
    HF_TOKEN=$(grep "^HF_TOKEN=" .env | cut -d '=' -f2- | tr -d '"' | tr -d "'")
fi

# 2. Si tenemos token, configurar remoto y hacer push
if [ -n "${HF_TOKEN:-}" ]; then
    echo "🔑 Configurando autenticación de Hugging Face..."
    git remote set-url hf "https://cero2k6:${HF_TOKEN}@huggingface.co/spaces/cero2k6/agente-agro-inteligente"
    echo "🚀 Enviando cambios a Hugging Face (Space)..."
    git push hf "$CURRENT_BRANCH:main" || echo "⚠️ Advertencia: Falló el push a Hugging Face."
fi
