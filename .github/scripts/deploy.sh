#!/bin/bash
# Script de deploy executado no servidor via AWS SSM.
# Variáveis obrigatórias: APP_DIR, DOWNLOAD_URL
set -e

VENV="$APP_DIR/venv/bin"

echo ""
echo "════════════════════════════════════════"
echo "  STREAMING FLIX — DEPLOY $(date '+%d/%m/%Y %H:%M:%S')"
echo "════════════════════════════════════════"

echo ""
echo "📥 [1/5] Baixando código..."
curl -sL -o /tmp/app_deploy.tar.gz "$DOWNLOAD_URL"

echo ""
echo "📦 [2/5] Extraindo código em $APP_DIR..."
mkdir -p "$APP_DIR"
tar xzf /tmp/app_deploy.tar.gz -C "$APP_DIR"
rm -f /tmp/app_deploy.tar.gz

echo ""
echo "📦 [3/5] Instalando dependências..."
"$VENV/pip" install -r "$APP_DIR/requirements.txt" --quiet

echo ""
echo "💾 [4/5] Backup do banco e migrations..."
cd "$APP_DIR"
cp db.sqlite3 "db.sqlite3.bak_$(date +%Y%m%d_%H%M%S)" 2>/dev/null || true
ls -t db.sqlite3.bak_* 2>/dev/null | tail -n +6 | xargs rm -f || true
"$VENV/python" manage.py migrate --noinput

echo ""
echo "🔄 [5/5] Reiniciando Gunicorn..."
systemctl restart gunicorn
sleep 2
systemctl is-active --quiet gunicorn \
  && echo "✅ Gunicorn rodando." \
  || (echo "❌ Gunicorn falhou ao iniciar!" && exit 1)

echo ""
echo "════════════════════════════════════════"
echo "  ✅ DEPLOY CONCLUÍDO COM SUCESSO"
echo "════════════════════════════════════════"
