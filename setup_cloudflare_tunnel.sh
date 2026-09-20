#!/bin/bash
# Stay4S Cloudflare Named Tunnel Setup
# Dit script bereidt alles voor. Mitchell hoeft alleen nog:
# 1. cloudflared tunnel login (opent browser)
# 2. DNS verhuizen naar Cloudflare
# 3. Dit script te runnen

set -e

CONFIG_DIR="$HOME/.cloudflared"
mkdir -p "$CONFIG_DIR"

echo "=== STAY4S CLOUDFLARE TUNNEL SETUP ==="
echo ""

# Check if already authenticated
if [ -f "$CONFIG_DIR/cert.pem" ]; then
    echo "[OK] Al geauthenticeerd met Cloudflare"
else
    echo "[!] Niet geauthenticeerd. Run eerst:"
    echo "    cloudflared tunnel login"
    echo "    (Opent browser, log in met Cloudflare account, selecteer stay4s.com)"
    echo ""
    echo "Na login, run dit script opnieuw."
    exit 1
fi

# Create tunnel
echo "=== TUNNEL AANMAKEN ==="
TUNNEL_NAME="stay4s"
TUNNEL_ID=$(cloudflared tunnel list 2>/dev/null | grep "$TUNNEL_NAME" | awk '{print $1}' || echo "")

if [ -z "$TUNNEL_ID" ]; then
    echo "Tunnel '$TUNNEL_NAME' bestaat niet, aanmaken..."
    cloudflared tunnel create "$TUNNEL_NAME"
    TUNNEL_ID=$(cloudflared tunnel list | grep "$TUNNEL_NAME" | awk '{print $1}')
    echo "Tunnel aangemaakt: ID=$TUNNEL_ID"
else
    echo "Tunnel '$TUNNEL_NAME' bestaat al: ID=$TUNNEL_ID"
fi

# Create config.yml
echo "=== CONFIG MAKEN ==="
cat > "$CONFIG_DIR/config.yml" << EOF
tunnel: $TUNNEL_ID
credentials-file: $CONFIG_DIR/$TUNNEL_ID.json

ingress:
  # Stay4Compa dashboard + chat
  - hostname: compa.stay4s.com
    service: http://localhost:8082
  
  # Geheim communicatie portaal (E2EE)
  - hostname: vault.stay4s.com
    service: http://localhost:8083
  
  # WhatsApp webhook + Stay4Safe AI API
  - hostname: api.stay4s.com
    service: http://localhost:8081
  
  # Stay4Safe AI landing page
  - hostname: safe.stay4s.com
    service: http://localhost:8081
  
  # Catch-all
  - service: http_status:404
EOF

echo "Config geschreven: $CONFIG_DIR/config.yml"
cat "$CONFIG_DIR/config.yml"

# Create DNS routes
echo ""
echo "=== DNS ROUTES AANMAKEN ==="
for SUBDOMAIN in compa vault api safe; do
    echo "  $SUBDOMAIN.stay4s.com -> $TUNNEL_ID"
    cloudflared tunnel route dns "$TUNNEL_NAME" "$SUBDOMAIN.stay4s.com" 2>/dev/null || \
    echo "  (bestaat al of handmatig toevoegen)"
done

# Update systemd service
echo ""
echo "=== SYSTEMD SERVICE UPDATEN ==="
sudo tee /etc/systemd/system/cloudflared.service > /dev/null << EOF
[Unit]
Description=Cloudflare Named Tunnel for Stay4S
After=network.target

[Service]
Type=simple
User=Miesdevries
ExecStart=/usr/local/bin/cloudflared tunnel run stay4s
Restart=always
RestartSec=10
Environment=TUNNEL_LOGLEVEL=info

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl restart cloudflared
sleep 3
echo "Service status: $(sudo systemctl is-active cloudflared)"

# Test
echo ""
echo "=== TEST ==="
echo "Testing compa.stay4s.com..."
curl -s --max-time 10 "https://compa.stay4s.com/health" 2>&1 | head -1 || echo "(nog niet bereikbaar -- DNS moet propagaten)"

echo ""
echo "=== KLAAR ==="
echo "Tunnel: $TUNNEL_NAME (ID: $TUNNEL_ID)"
echo "Subdomains:"
echo "  compa.stay4s.com -> :8082 (Stay4Compa)"
echo "  vault.stay4s.com -> :8083 (Vault)"
echo "  api.stay4s.com   -> :8081 (WhatsApp API)"
echo "  safe.stay4s.com  -> :8081 (Stay4Safe AI)"
echo ""
echo "Volgende stappen:"
echo "1. Verhuis stay4s.com DNS naar Cloudflare (via IONOS nameserver change)"
echo "2. Wacht tot DNS propageert (kan 1-24u duren)"
echo "3. Test: curl https://compa.stay4s.com/health"