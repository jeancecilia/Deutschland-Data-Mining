#!/bin/sh
set -eu

ufw default deny incoming
ufw default allow outgoing
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp

if [ "${ALLOW_UPTIME_KUMA:-0}" = "1" ]; then
  ufw allow 3001/tcp
fi

ufw --force enable
ufw status verbose
