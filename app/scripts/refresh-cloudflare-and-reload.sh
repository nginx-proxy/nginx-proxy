#!/usr/bin/env bash
# Cron job: refresh Cloudflare real IP ranges, reload nginx only when they changed.
# If the new file breaks `nginx -t`, the previous file is restored and nginx is not reloaded.
set -uo pipefail

TARGET_CONF="${CF_REAL_IP_CONF:-/etc/nginx/conf.d/cloudflare.conf}"
BACKUP_CONF="${TARGET_CONF}.bak"
LOCK_FILE="/var/run/cf-refresh.lock"

log() { echo "[cf-refresh] $(date -u +'%Y-%m-%dT%H:%M:%SZ') $*"; }

# One run at a time (a slow download must not overlap with the next schedule).
exec 9>"${LOCK_FILE}"
if ! flock -n 9; then
  log "another refresh is running, skipping"
  exit 0
fi

rm -f "${BACKUP_CONF}"
[ -f "${TARGET_CONF}" ] && cp -p "${TARGET_CONF}" "${BACKUP_CONF}"

/app/scripts/update-cloudflare-real-ip.sh
rc=$?
case "${rc}" in
  0) ;;
  3) log "ranges unchanged, no reload"; rm -f "${BACKUP_CONF}"; exit 0 ;;
  *) log "update failed (rc=${rc}), existing config kept"; rm -f "${BACKUP_CONF}"; exit 1 ;;
esac

if test_output="$(nginx -t -c /etc/nginx/nginx.conf 2>&1)"; then
  if nginx -s reload; then
    log "ranges changed, nginx reloaded"
  else
    log "nginx reload failed"
    rm -f "${BACKUP_CONF}"
    exit 1
  fi
else
  log "nginx -t failed with new ranges, restoring previous config:"
  printf '%s\n' "${test_output}" | grep -E 'emerg|error' | sed 's/^/[cf-refresh]   /'
  if [ -f "${BACKUP_CONF}" ]; then
    mv -f "${BACKUP_CONF}" "${TARGET_CONF}"
  else
    rm -f "${TARGET_CONF}"
  fi
  exit 1
fi

rm -f "${BACKUP_CONF}"
