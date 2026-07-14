#!/usr/bin/env bash
# Let's Encrypt initial certificate (Sprint 11)
# Usage: ./certbot-init.sh your-domain.example.com admin@example.com
set -euo pipefail
DOMAIN="${1:?Domain required}"
EMAIL="${2:?Email required}"
docker compose -f docker-compose.production.yml run --rm certbot certonly \
  --webroot -w /var/www/certbot \
  -d "$DOMAIN" \
  --email "$EMAIL" --agree-tos --no-eff-email
# Symlink or copy to deploy/ssl/
cp -L "deploy/ssl/live/$DOMAIN/fullchain.pem" deploy/ssl/fullchain.pem
cp -L "deploy/ssl/live/$DOMAIN/privkey.pem" deploy/ssl/privkey.pem
echo "Certificates installed for $DOMAIN"
