#!/bin/sh
set -e

if [ -z "$DOMAIN" ]; then
  echo "ERROR: DOMAIN not set"
  exit 1
fi

CONF="/etc/nginx/conf.d/default.conf"

echo "ENV=$ENV DOMAIN=$DOMAIN"

if [ "$ENV" = "dev" ]; then
  echo "Starting in DEV (HTTP only)"

  cat <<EOF > $CONF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;

    location / {
        proxy_pass http://app:8501;

        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";

        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}
EOF

else
  echo "Starting in PROD"

  CERT_PATH="/etc/letsencrypt/live/$DOMAIN/fullchain.pem"

  if [ -f "$CERT_PATH" ]; then
    echo "Certificate found → HTTPS mode"

    envsubst '${DOMAIN}' \
      < /etc/nginx/templates/app.conf.template \
      > $CONF

  else
    echo "No certificate yet → HTTP fallback (for certbot)"

    cat <<EOF > $CONF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        proxy_pass http://app:8501;
    }
}
EOF
  fi
fi

nginx -g 'daemon off;'
