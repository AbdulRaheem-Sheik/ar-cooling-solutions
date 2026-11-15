#!/usr/bin/env bash
# Sets up (or updates) the AR Cooling Solutions website on an Oracle Cloud Ubuntu server.
#
#   First time:   curl -fsSL https://raw.githubusercontent.com/AbdulRaheem-Sheik/ar-cooling-solutions/main/deploy/oracle/setup.sh -o setup.sh
#                 sudo bash setup.sh arcooling.in
#   Update later: sudo bash /opt/ar-cooling/deploy/oracle/setup.sh arcooling.in
#
# Optional second argument: the git branch to run (default: main).
# Safe to run again: it updates the code and keeps the database and settings.
#
# What it sets up:
#   /opt/ar-cooling              the code (from GitHub) and its Python packages
#   /var/lib/ar-cooling/         the content database (survives updates)
#   /etc/ar-cooling.env          secret key, admin login and settings (private)
#   ar-cooling service           runs the app (serve.py), restarts it if it stops
#   Caddy                        HTTPS for the domain, forwards visitors to the app
set -euo pipefail

REPO="https://github.com/AbdulRaheem-Sheik/ar-cooling-solutions.git"
APP_DIR=/opt/ar-cooling
DATA_DIR=/var/lib/ar-cooling
ENV_FILE=/etc/ar-cooling.env
APP_USER=arcooling

main() {   # everything runs inside a function, so updating this file mid-run is safe
  local domain="${1:-}" branch="${2:-main}"
  if [[ -z "$domain" ]]; then
    echo "Usage: sudo bash setup.sh <domain> [branch]    e.g. sudo bash setup.sh arcooling.in" >&2
    exit 1
  fi
  if [[ $EUID -ne 0 ]]; then
    echo "Run it with sudo." >&2
    exit 1
  fi

  step "Adding swap space (spare memory on disk, for 1 GB servers)"
  if ! swapon --show | grep -q /swapfile; then
    if [[ ! -f /swapfile ]]; then
      fallocate -l 2G /swapfile
      chmod 600 /swapfile
      mkswap /swapfile >/dev/null
    fi
    swapon /swapfile
    grep -q '^/swapfile ' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
  fi
  free -h | sed -n '1,3p'

  step "Installing system packages (Python, git, Caddy)"
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -q
  apt-get install -y -q python3 python3-venv git caddy iptables-persistent

  step "Opening ports 80 and 443 in the server's firewall"
  # Oracle's Ubuntu images block everything except SSH by default.
  for port in 80 443; do
    iptables -C INPUT -p tcp --dport "$port" -m state --state NEW -j ACCEPT 2>/dev/null \
      || iptables -I INPUT 1 -p tcp --dport "$port" -m state --state NEW -j ACCEPT
  done
  netfilter-persistent save

  step "Creating the app user and folders"
  id "$APP_USER" &>/dev/null || useradd --system --home-dir "$APP_DIR" --shell /usr/sbin/nologin "$APP_USER"
  install -d -o "$APP_USER" -g "$APP_USER" -m 750 "$DATA_DIR"

  step "Getting the code (branch: $branch)"
  if [[ -d "$APP_DIR/.git" ]]; then
    git -C "$APP_DIR" fetch -q origin "$branch"
    git -C "$APP_DIR" checkout -q -B "$branch" "origin/$branch"
  else
    git clone -q --branch "$branch" "$REPO" "$APP_DIR"
  fi

  step "Installing Python packages"
  [[ -d "$APP_DIR/.venv" ]] || python3 -m venv "$APP_DIR/.venv"
  "$APP_DIR/.venv/bin/pip" install -q --upgrade pip
  "$APP_DIR/.venv/bin/pip" install -q -r "$APP_DIR/requirements.txt"

  step "Writing settings ($ENV_FILE)"
  if [[ ! -f "$ENV_FILE" ]]; then
    local key
    key="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
    cat > "$ENV_FILE" <<EOF
# AR Cooling Solutions server settings. Private: readable by root only.
# After changing anything here: sudo systemctl restart ar-cooling
SECRET_KEY=$key
AR_SITE_URL=https://$domain
AR_DATABASE_PATH=$DATA_DIR/ar_cooling.db
AR_BEHIND_PROXY=1
AR_HOST=127.0.0.1
AR_PORT=8080

# Admin login (/admin). Disabled until both are set; password 12+ characters.
AR_ADMIN_USERNAME=
AR_ADMIN_PASSWORD=
EOF
    echo "Created $ENV_FILE with a new secret key."
  else
    echo "Keeping existing $ENV_FILE."
  fi
  chmod 600 "$ENV_FILE"

  step "Installing the ar-cooling service"
  install -m 644 "$APP_DIR/deploy/oracle/ar-cooling.service" /etc/systemd/system/ar-cooling.service
  systemctl daemon-reload
  systemctl enable -q ar-cooling
  systemctl restart ar-cooling

  step "Configuring Caddy (HTTPS) for $domain"
  sed "s/{DOMAIN}/$domain/g" "$APP_DIR/deploy/oracle/Caddyfile" > /etc/caddy/Caddyfile
  caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile >/dev/null
  systemctl enable -q caddy
  systemctl reload caddy || systemctl restart caddy

  step "Checking the app answers"
  local ok=""
  for _ in $(seq 1 15); do
    if curl -fsS -o /dev/null http://127.0.0.1:8080/; then ok=1; break; fi
    sleep 1
  done
  if [[ -z "$ok" ]]; then
    echo "The app did not start. See: sudo journalctl -u ar-cooling -n 50" >&2
    exit 1
  fi

  local ip
  ip="$(curl -fsS -4 --max-time 5 https://ifconfig.me 2>/dev/null || echo '<server IP>')"
  cat <<EOF

Done. The website is running.
  Test it now:        http://$ip
  After DNS points $domain at $ip:  https://$domain (HTTPS is set up automatically)
  Admin login:        set AR_ADMIN_USERNAME and AR_ADMIN_PASSWORD in $ENV_FILE,
                      then: sudo systemctl restart ar-cooling
  App logs:           sudo journalctl -u ar-cooling -f
EOF
}

step() { printf '\n==> %s\n' "$1"; }

main "$@"
