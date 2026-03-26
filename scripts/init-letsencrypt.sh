#!/bin/sh
set -e

if [ "$ENV" != "prod" ]; then
  echo "Skipping certbot init (ENV=$ENV)"
  exit 0
fi

if [ -z "$DOMAIN" ] || [ -z "$EMAIL" ]; then
  echo "DOMAIN or EMAIL not set"
  exit 1
fi

CERT_PATH="/etc/letsencrypt/live/$DOMAIN/fullchain.pem"

if [ -f "$CERT_PATH" ]; then
  echo "Certificate already exists"
  exit 0
fi

echo "Requesting certificate for $DOMAIN"

certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  -d $DOMAIN \
  -d www.$DOMAIN \
  --email $EMAIL \
  --agree-tos \
  --no-eff-email
