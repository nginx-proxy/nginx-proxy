#!/usr/bin/env bash
set -euo pipefail

echo "[cf-refresh] Updating Cloudflare real IP ranges..."
/app/scripts/update-cloudflare-real-ip.sh

echo "[cf-refresh] Testing Nginx configuration..."
if nginx -t -c /etc/nginx/nginx.conf; then
  echo "[cf-refresh] Nginx config OK. Reloading..."
  nginx -s reload
  echo "[cf-refresh] Reload done."
else
  echo "[cf-refresh] Nginx config test failed, not reloading." >&2
  exit 1
fi


