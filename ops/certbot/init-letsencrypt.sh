#!/bin/sh
set -eu

DOMAIN="${1:?domain is required}"
EMAIL="${2:?email is required}"
ROOT_DIR="$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd)"

mkdir -p "$ROOT_DIR/nginx/certbot/www" "$ROOT_DIR/nginx/certbot/conf"

docker compose --project-directory "$ROOT_DIR" --profile prod run --rm certbot certonly \
  --webroot \
  --webroot-path /var/www/certbot \
  --email "$EMAIL" \
  --agree-tos \
  --no-eff-email \
  -d "$DOMAIN"
