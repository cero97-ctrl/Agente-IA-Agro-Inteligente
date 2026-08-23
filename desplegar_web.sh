#!/usr/bin/env bash
# desplegar_web.sh — Despliega la web del agente en HuggingFace Spaces
#
# REGLA CLAVE: el redespliegue lo dispara `git push hf main` (el repositorio del
# propio Space), NUNCA GitHub. Este script encapsula el flujo completo:
#
#   1. Verifica que estás en el repo correcto y muestra cambios sin commitear
#      (opción de commitearlos antes de desplegar).
#   2. Muestra los commits pendientes respecto al Space y pide confirmación.
#   3. Hace push al remoto `hf`.
#   4. Monitorea el build del Space vía API hasta RUNNING o error.
#   5. Verifica que la web responde HTTP 200.
#
# Uso:
#   ./desplegar_web.sh            # flujo interactivo completo
#   ./desplegar_web.sh --check    # solo simula: muestra qué se desplegaría
#   ./desplegar_web.sh -y         # sin confirmaciones (usa -m para el mensaje de commit)
#   ./desplegar_web.sh -y -m "mensaje"
set -euo pipefail

SPACE_ID="cero2k6/agente-agro-inteligent"
SPACE_URL="https://cero2k6-agente-agro-inteligent.hf.space"
API="https://huggingface.co/api/spaces/${SPACE_ID}"
REMOTE="hf"
BRANCH="main"
MAX_WAIT=900          # segundos máximos de espera del build
INTERVALO=20          # segundos entre consultas de estado

AUTO=no; MSG=""; CHECK=no
while [[ $# -gt 0 ]]; do
  case "$1" in
    --check) CHECK=yes; shift;;
    -y|--yes) AUTO=yes; shift;;
    -m|--message) MSG="$2"; shift 2;;
    -h|--help) sed -n '2,22p' "$0"; exit 0;;
    *) echo "Arg desconocido: $1 (-h para ayuda)"; exit 1;;
  esac
done

paso() { echo; echo "━━━ $1 ━━━"; }

# ── 0. Contexto ───────────────────────────────────────────────────────────────
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || { echo "✗ No es un repo git."; exit 1; }
git remote get-url "$REMOTE" >/dev/null 2>&1 || { echo "✗ Falta el remoto '$REMOTE'."; exit 1; }

# ── 1. Cambios sin commitear ────────────────────────────────────────────────
paso "1/5 Cambios sin commitear"
if ! git diff-index --quiet HEAD -- 2>/dev/null || [ -n "$(git ls-files --others --exclude-standard)" ]; then
  git status --short | head -20
  n=$(git status --porcelain | wc -l)
  echo "→ $n elemento(s) SIN commitear: NO se incluirán en el despliegue."
  if [ "$CHECK" = yes ]; then exit 0; fi
  if [ "$AUTO" = yes ] && [ -n "$MSG" ]; then RESP=y
  else
    read -rp "¿Commitear todo ahora${MSG:+ con: \"$MSG\"}? [y/N]: " RESP
  fi
  if [[ "${RESP:-n}" =~ ^[Yy]$ ]]; then
    m="${MSG:-Despliegue web: cambios previos vía desplegar_web.sh}"
    git add -A && git commit -q -m "$m" && echo "✓ Commit creado: $(git log -1 --format=%h)"
  else
    echo "✗ Cancelado. Commitea primero (o reintenta aceptando el commit)."; exit 1
  fi
else
  echo "✓ Árbol limpio."
fi

# ── 2. Qué se desplegaría ────────────────────────────────────────────────────
paso "2/5 Commits pendientes respecto al Space"
git fetch "$REMOTE" "$BRANCH" -q
PENDIENTES=$(git log --oneline "${REMOTE}/${BRANCH}..HEAD")
if [ -z "$PENDIENTES" ]; then
  echo "✓ El Space ya está en el commit local. Nada que desplegar."
  echo "  (Si esperabas cambios: ¿quizá faltó commitear?)"
  exit 0
fi
echo "$PENDIENTES"
total=$(echo "$PENDIENTES" | wc -l)
echo "→ $total commit(s) por desplegar."
[ "$CHECK" = yes ] && { echo "(modo --check: no se hizo nada más)"; exit 0; }

if [ "$AUTO" != yes ]; then
  read -rp "¿Desplegar AHORA a ${SPACE_ID}? [y/N]: " RESP
  [[ "${RESP:-n}" =~ ^[Yy]$ ]] || { echo "Cancelado."; exit 1; }
fi

# ── 3. Push ──────────────────────────────────────────────────────────────────
paso "3/5 Push al Space (${REMOTE}/${BRANCH})"
GIT_TERMINAL_PROMPT=0 git push "$REMOTE" "$BRANCH" || {
  echo "✗ Falló el push. Si pidió credenciales, configura: git config --global credential.helper store"; exit 1;
}
sha=$(git rev-parse --short HEAD)
echo "✓ Enviado. El Space reconstruirá desde $sha"

# ── 4. Monitoreo del build ───────────────────────────────────────────────────
paso "4/5 Monitoreando build (máx ${MAX_WAIT}s)"
ultimo=""; t=0
while [ $t -lt $MAX_WAIT ]; do
  stage=$(curl -s "$API" | python3 -c "import json,sys; print(json.load(sys.stdin).get('runtime',{}).get('stage','DESCONOCIDO'))" 2>/dev/null || echo "?")
  if [ "$stage" != "$ultimo" ]; then echo "  [$(date +%H:%M:%S)] stage: $stage"; ultimo="$stage"; fi
  case "$stage" in
    RUNNING)        echo "✓ ¡Space en marcha!"; break;;
    BUILD_ERROR)    echo "✗ Error de construcción. Logs: ${API}/logs/build"; exit 1;;
    RUNTIME_ERROR)  echo "✗ La app arrancó y cayó. Logs: https://huggingface.co/spaces/${SPACE_ID}/logs/run"; exit 1;;
    NO_APP_FILE)    echo "✗ HF no encuentra el Dockerfile/app en el repo del Space."; exit 1;;
  esac
  sleep "$INTERVALO"; t=$((t+INTERVALO))
done
[ "$stage" = "RUNNING" ] || { echo "✗ Timeout esperando el build (último estado: $stage). Revisa: https://huggingface.co/spaces/${SPACE_ID}"; exit 1; }

# ── 5. Verificación final ────────────────────────────────────────────────────
paso "5/5 Verificación HTTP"
sleep 5
code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 30 "$SPACE_URL")
if [ "$code" = "200" ]; then
  echo "✓ Web operativa: $SPACE_URL (HTTP 200)"
else
  echo "⚠️ Responde HTTP $code (a veces tarda unos segundos tras RUNNING). Reintenta manualmente."
fi
