#!/usr/bin/env bash
#
# Despliega la rama master en el servidor de producción SIN pasar por GitHub,
# usando un git bundle (ver DEPLOY_BUNDLE.md).
#
# Se ejecuta desde la máquina de desarrollo, en la raíz del repo:
#
#   ./scripts/deploy_bundle.sh [usuario@servidor]
#
# Por defecto usa $ARCA_SERVER o, si no está definida, sebastianr@172.16.140.98.
#
# Pasos:
#   1. Verifica que no haya cambios sin commitear.
#   2. Crea el bundle con la rama master.
#   3. Lo copia al servidor con scp.
#   4. En el servidor (como usuario arca): verifica el bundle, hace fetch
#      y merge --ff-only, y reinstala dependencias si cambió requirements.txt.
#
# No ejecuta el scraper: eso queda a cargo del timer o de un start manual.

set -euo pipefail

SERVER="${1:-${ARCA_SERVER:-sebastianr@172.16.140.98}}"
BRANCH="master"
REMOTE_DIR="/opt/arca_scraper"
BUNDLE_NAME="arca_scraper_$(date +%Y%m%d_%H%M%S).bundle"
LOCAL_BUNDLE="$(mktemp -d)/${BUNDLE_NAME}"
REMOTE_BUNDLE="/tmp/${BUNDLE_NAME}"

cd "$(git rev-parse --show-toplevel)"

# 1. El bundle solo lleva commits: si hay cambios sin commitear no se desplegarían.
if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
    echo "ERROR: hay cambios sin commitear. Commiteá antes de desplegar:" >&2
    git status --short --untracked-files=no >&2
    exit 1
fi

if [ "$(git rev-parse --abbrev-ref HEAD)" != "$BRANCH" ]; then
    echo "AVISO: estás en '$(git rev-parse --abbrev-ref HEAD)'; se despliega '$BRANCH' igualmente."
fi

echo "==> Commit a desplegar:"
git log -1 --oneline "$BRANCH"

# 2. Crear el bundle (el repo es chico, se incluye la historia completa de master).
echo "==> Creando bundle ${LOCAL_BUNDLE}"
git bundle create "$LOCAL_BUNDLE" "$BRANCH"

# 3. Copiar al servidor. /tmp es legible por el usuario arca.
echo "==> Copiando bundle a ${SERVER}:${REMOTE_BUNDLE}"
scp "$LOCAL_BUNDLE" "${SERVER}:${REMOTE_BUNDLE}"
rm -f "$LOCAL_BUNDLE"

# 4. Aplicar en el servidor. -t para que sudo pueda pedir la contraseña.
echo "==> Aplicando en el servidor (puede pedir la contraseña de sudo)"
ssh -t "$SERVER" "
    set -e
    chmod 644 '${REMOTE_BUNDLE}'
    cd '${REMOTE_DIR}'
    GIT='sudo -u arca git -C ${REMOTE_DIR}'

    echo '--- Verificando bundle'
    \$GIT bundle verify '${REMOTE_BUNDLE}'

    OLD_HEAD=\$(\$GIT rev-parse HEAD)
    echo \"--- Versión actual: \$(\$GIT log -1 --oneline)\"

    echo '--- Fetch desde el bundle'
    \$GIT fetch '${REMOTE_BUNDLE}' '${BRANCH}'

    echo '--- Merge (solo fast-forward)'
    \$GIT merge --ff-only FETCH_HEAD

    echo \"--- Versión desplegada: \$(\$GIT log -1 --oneline)\"

    if ! \$GIT diff --quiet \"\$OLD_HEAD\" HEAD -- requirements.txt; then
        echo '--- requirements.txt cambió: instalando dependencias'
        sudo -u arca '${REMOTE_DIR}/venv/bin/pip' install -r '${REMOTE_DIR}/requirements.txt'
    fi

    rm -f '${REMOTE_BUNDLE}'
    echo '--- Listo'
"

echo
echo "Despliegue completado. Para probar ahora mismo en el servidor:"
echo "  sudo systemctl start arca-scraper.service"
echo "  sudo journalctl -u arca-scraper.service -f"
