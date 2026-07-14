#!/usr/bin/env bash
# Generate self-signed SSL certificate for internal/production testing (Sprint 11)
set -euo pipefail
DIR="$(cd "$(dirname "$0")/.." && pwd)/deploy/ssl"
mkdir -p "$DIR"
DOMAIN="${1:-localhost}"
DAYS="${2:-365}"
openssl req -x509 -nodes -days "$DAYS" -newkey rsa:4096 \
  -keyout "$DIR/privkey.pem" \
  -out "$DIR/fullchain.pem" \
  -subj "/CN=$DOMAIN/O=AEMS/C=VN"
echo "Self-signed cert created in $DIR (CN=$DOMAIN, valid $DAYS days)"
