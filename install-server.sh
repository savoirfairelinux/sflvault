#!/usr/bin/env bash
# install-server.sh — Deploy the SFLvault server (Python 3) on Ubuntu Server.
#
# Usage:
#   sudo ./install-server.sh --config /path/to/production.ini --db /path/to/sflvault.sqlite
#
# Required:
#   --config <file>     Path to an existing production.ini configuration file
#   --db     <file>     Path to an existing sflvault.sqlite database file
#
# Optional:
#   --repo-dir  <dir>   Path to the sflvault git repository (default: directory of this script)
#   --venv      <dir>   Path for the Python virtualenv (default: /opt/sflvault-env)
#   --install   <dir>   Base install directory (default: /opt/SFLvault)
#   --port      <num>   Port the server listens on (default: 5000)
#   --no-nginx          Skip nginx reverse-proxy setup
#
# What this script does:
#   1. Installs system packages (python3, python3-venv, nginx)
#   2. Creates the 'sflvault' system user if it does not exist
#   3. Creates directory layout under --install
#   4. Copies production.ini and sflvault.sqlite from --data-dir
#   5. Creates a Python virtualenv and installs sflvault-common + sflvault-server
#   6. Installs the systemd unit file and starts/enables the service
#   7. Optionally configures nginx as SSL-terminating reverse proxy
#
set -euo pipefail

# ── helpers ──────────────────────────────────────────────────────────────────
die()  { echo "ERROR: $*" >&2; exit 1; }
info() { echo "==> $*"; }

require_root() {
    [[ $EUID -eq 0 ]] || die "This script must be run as root (sudo $0 $*)"
}

# ── defaults ─────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$SCRIPT_DIR"
VENV_DIR="/opt/sflvault-env"
INSTALL_DIR="/opt/SFLvault"
PORT=5000
CONFIG_FILE=""
DB_FILE=""
SETUP_NGINX=true

# ── argument parsing ──────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --config)    CONFIG_FILE="$2"; shift 2 ;;
        --db)        DB_FILE="$2";     shift 2 ;;
        --repo-dir)  REPO_DIR="$2";    shift 2 ;;
        --venv)      VENV_DIR="$2";    shift 2 ;;
        --install)   INSTALL_DIR="$2"; shift 2 ;;
        --port)      PORT="$2";        shift 2 ;;
        --no-nginx)  SETUP_NGINX=false; shift ;;
        -h|--help)
            sed -n '2,14p' "$0" | sed 's/^# \?//'
            exit 0
            ;;
        *) die "Unknown option: $1" ;;
    esac
done

require_root

[[ -n "$CONFIG_FILE" ]] || die "--config is required"
[[ -n "$DB_FILE" ]]     || die "--db is required"
[[ -f "$CONFIG_FILE" ]] || die "Configuration file not found: $CONFIG_FILE"
[[ -f "$DB_FILE" ]]     || die "Database file not found: $DB_FILE"

COMMON_DIR="$REPO_DIR/common"
SERVER_DIR="$REPO_DIR/server"
[[ -f "$COMMON_DIR/setup.py" ]] || die "common/setup.py not found — is --repo-dir pointing at the sflvault repo?"
[[ -f "$SERVER_DIR/setup.py" ]] || die "server/setup.py not found — is --repo-dir pointing at the sflvault repo?"

# ── git pull ──────────────────────────────────────────────────────────────────
if git -C "$REPO_DIR" rev-parse --is-inside-work-tree &>/dev/null; then
    info "Updating repository..."
    git -C "$REPO_DIR" pull --ff-only || echo "WARNING: git pull failed, installing from current state"
fi

# ── system packages ───────────────────────────────────────────────────────────
info "Installing system packages..."
apt-get update -qq
PACKAGES=(python3 python3-venv python3-pip libssl-dev)
$SETUP_NGINX && PACKAGES+=(nginx)
apt-get install -y -qq "${PACKAGES[@]}"

# ── sflvault system user ──────────────────────────────────────────────────────
if ! id -u sflvault &>/dev/null; then
    info "Creating 'sflvault' system user..."
    useradd --system --no-create-home --shell /usr/sbin/nologin sflvault
else
    info "'sflvault' user already exists"
fi

# ── resolve absolute paths ────────────────────────────────────────────────────
CONFIG_FILE="$(realpath "$CONFIG_FILE")"
DB_FILE="$(realpath "$DB_FILE")"
DB_DIR="$(dirname "$DB_FILE")"

# ── directory layout (virtualenv only) ───────────────────────────────────────
info "Creating install directory $INSTALL_DIR ..."
mkdir -p "$INSTALL_DIR"

# ── virtualenv ────────────────────────────────────────────────────────────────
info "Setting up Python virtualenv at $VENV_DIR ..."
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --quiet --upgrade pip
info "Installing sflvault-common and sflvault-server..."
"$VENV_DIR/bin/pip" install --quiet --force-reinstall \
    "$COMMON_DIR" "$SERVER_DIR"

# ── permissions — sflvault user must be able to read config and write DB ──────
info "Setting ownership and permissions..."
chown sflvault:sflvault "$DB_FILE"
chmod 640 "$DB_FILE"
chown sflvault:sflvault "$DB_DIR"
chmod 750 "$DB_DIR"
chown root:sflvault "$CONFIG_FILE"
chmod 640 "$CONFIG_FILE"

# ── systemd unit ─────────────────────────────────────────────────────────────
info "Installing systemd unit file..."
cat > /etc/systemd/system/sflvault-server.service <<EOF
[Unit]
Description=SFLvault Secure Credential Store Server
Documentation=https://www.sflvault.org
After=network.target

[Service]
Type=simple
User=sflvault
Group=sflvault

WorkingDirectory=$INSTALL_DIR
ExecStart=$VENV_DIR/bin/python -m sflvault.server $CONFIG_FILE

Restart=on-failure
RestartSec=5

StandardOutput=journal
StandardError=journal
SyslogIdentifier=sflvault

NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$DB_DIR
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable sflvault-server
systemctl restart sflvault-server
sleep 3

if systemctl is-active --quiet sflvault-server; then
    info "sflvault-server is running"
else
    echo "ERROR: sflvault-server failed to start. Check: journalctl -u sflvault-server -n 30" >&2
    exit 1
fi

# ── nginx ─────────────────────────────────────────────────────────────────────
if $SETUP_NGINX; then
    info "Configuring nginx reverse proxy..."
    NGINX_CONF="/etc/nginx/sites-available/sflvault"
    cat > "$NGINX_CONF" <<EOF
# SFLvault nginx reverse proxy
# Place your SSL certificate at /etc/nginx/ssl/sflvault.crt and key at
# /etc/nginx/ssl/sflvault.key before enabling HTTPS.
server {
    listen 80;
    listen [::]:80;
    server_name _;

    location /vault/ {
        proxy_pass http://127.0.0.1:${PORT}/vault/;
        proxy_set_header Host \$host;
        proxy_read_timeout 120s;
    }
}

# Uncomment and configure this block to enable HTTPS:
# server {
#     listen 443 ssl;
#     listen [::]:443 ssl;
#     server_name your.hostname.example.com;
#
#     ssl_certificate     /etc/nginx/ssl/sflvault.crt;
#     ssl_certificate_key /etc/nginx/ssl/sflvault.key;
#     ssl_protocols       TLSv1.2 TLSv1.3;
#     ssl_ciphers         HIGH:!aNULL:!MD5;
#
#     location /vault/ {
#         proxy_pass http://127.0.0.1:${PORT}/vault/;
#         proxy_set_header Host \$host;
#         proxy_read_timeout 120s;
#     }
# }
EOF

    # Enable site if not already
    ln -sf "$NGINX_CONF" /etc/nginx/sites-enabled/sflvault

    # Remove default site to avoid conflicts
    rm -f /etc/nginx/sites-enabled/default

    nginx -t && systemctl reload nginx
    info "nginx configured. Edit $NGINX_CONF to enable HTTPS."
fi

# ── summary ───────────────────────────────────────────────────────────────────
echo ""
echo "┌─────────────────────────────────────────────────────────┐"
echo "│          SFLvault server installation complete           │"
echo "├─────────────────────────────────────────────────────────┤"
printf "│  Config:    %-44s│\n" "$CONFIG_FILE"
printf "│  Database:  %-44s│\n" "$DB_FILE"
printf "│  Virtualenv:%-44s│\n" "$VENV_DIR"
printf "│  Service:   %-44s│\n" "systemctl status sflvault-server"
$SETUP_NGINX && printf "│  nginx:     %-44s│\n" "$NGINX_CONF"
echo "└─────────────────────────────────────────────────────────┘"
echo ""
echo "Manage the service with:"
echo "  systemctl {start|stop|restart|status} sflvault-server"
echo "  journalctl -u sflvault-server -f"

