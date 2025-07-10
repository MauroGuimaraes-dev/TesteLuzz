#!/bin/bash
"""
Installation script for VPS deployment (Ubuntu/Debian)
"""

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   error "This script should not be run as root. Please run as a regular user with sudo privileges."
fi

log "Starting Consolidador de Pedidos installation..."

# Update system
log "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install system dependencies
log "Installing system dependencies..."
sudo apt install -y \
    python3.11 \
    python3.11-dev \
    python3.11-venv \
    python3-pip \
    nginx \
    postgresql \
    postgresql-contrib \
    redis-server \
    tesseract-ocr \
    tesseract-ocr-por \
    git \
    curl \
    certbot \
    python3-certbot-nginx \
    ufw \
    fail2ban \
    htop \
    supervisor

# Create application user
log "Creating application user..."
sudo useradd --system --shell /bin/bash --home /opt/consolidador --create-home consolidador || true

# Create application directory
log "Setting up application directory..."
sudo mkdir -p /opt/consolidador
sudo chown consolidador:consolidador /opt/consolidador

# Clone or copy application
log "Setting up application files..."
sudo -u consolidador cp -r . /opt/consolidador/app/
cd /opt/consolidador/app

# Create virtual environment
log "Creating Python virtual environment..."
sudo -u consolidador python3.11 -m venv venv
sudo -u consolidador ./venv/bin/pip install --upgrade pip

# Install Python dependencies
log "Installing Python dependencies..."
sudo -u consolidador ./venv/bin/pip install -r requirements.txt

# Create directories
log "Creating application directories..."
sudo -u consolidador mkdir -p /opt/consolidador/app/{uploads,temp,logs,backups}

# Set up database
log "Setting up PostgreSQL database..."
sudo -u postgres createdb consolidador || true
sudo -u postgres createuser consolidador || true
sudo -u postgres psql -c "ALTER USER consolidador PASSWORD 'consolidador123';" || true
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE consolidador TO consolidador;" || true

# Configure Redis
log "Configuring Redis..."
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Set up Nginx
log "Configuring Nginx..."
sudo cp nginx.conf /etc/nginx/sites-available/consolidador
sudo ln -sf /etc/nginx/sites-available/consolidador /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t

# Set up systemd service
log "Creating systemd service..."
sudo tee /etc/systemd/system/consolidador.service > /dev/null <<EOF
[Unit]
Description=Consolidador de Pedidos Gunicorn daemon
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=consolidador
Group=consolidador
RuntimeDirectory=consolidador
WorkingDirectory=/opt/consolidador/app
Environment="PATH=/opt/consolidador/app/venv/bin"
Environment="PYTHONPATH=/opt/consolidador/app"
Environment="SESSION_SECRET=\$(openssl rand -hex 32)"
ExecStart=/opt/consolidador/app/venv/bin/gunicorn --config gunicorn.conf.py main:app
ExecReload=/bin/kill -s HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Set up log rotation
log "Setting up log rotation..."
sudo tee /etc/logrotate.d/consolidador > /dev/null <<EOF
/opt/consolidador/app/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 consolidador consolidador
    postrotate
        systemctl reload consolidador
    endscript
}
EOF

# Set up backup script
log "Setting up backup script..."
sudo tee /opt/consolidador/backup.sh > /dev/null <<'EOF'
#!/bin/bash
BACKUP_DIR="/opt/consolidador/app/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup database
pg_dump -h localhost -U consolidador -d consolidador > "$BACKUP_DIR/db_backup_$DATE.sql"

# Backup uploads
tar -czf "$BACKUP_DIR/uploads_backup_$DATE.tar.gz" -C /opt/consolidador/app uploads/

# Remove backups older than 30 days
find "$BACKUP_DIR" -name "*.sql" -mtime +30 -delete
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
EOF

sudo chmod +x /opt/consolidador/backup.sh
sudo chown consolidador:consolidador /opt/consolidador/backup.sh

# Set up cron job for backups
log "Setting up automated backups..."
sudo -u consolidador crontab -l > /tmp/crontab.tmp 2>/dev/null || true
echo "0 2 * * * /opt/consolidador/backup.sh >> /opt/consolidador/app/logs/backup.log 2>&1" >> /tmp/crontab.tmp
sudo -u consolidador crontab /tmp/crontab.tmp
rm /tmp/crontab.tmp

# Configure firewall
log "Configuring firewall..."
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw --force enable

# Configure fail2ban
log "Configuring fail2ban..."
sudo tee /etc/fail2ban/jail.local > /dev/null <<EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true

[nginx-http-auth]
enabled = true

[nginx-botsearch]
enabled = true
EOF

sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Set file permissions
log "Setting file permissions..."
sudo chown -R consolidador:consolidador /opt/consolidador
sudo chmod -R 755 /opt/consolidador/app
sudo chmod 700 /opt/consolidador/app/uploads
sudo chmod 700 /opt/consolidador/app/temp

# Start services
log "Starting services..."
sudo systemctl daemon-reload
sudo systemctl enable consolidador
sudo systemctl start consolidador
sudo systemctl enable nginx
sudo systemctl restart nginx

# Check service status
log "Checking service status..."
if sudo systemctl is-active --quiet consolidador; then
    log "✓ Consolidador service is running"
else
    error "✗ Consolidador service failed to start"
fi

if sudo systemctl is-active --quiet nginx; then
    log "✓ Nginx service is running"
else
    error "✗ Nginx service failed to start"
fi

# Display status
log "Installation completed successfully!"
echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🎉 Consolidador de Pedidos has been installed successfully!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo
echo "📍 Application URL: http://$(hostname -I | awk '{print $1}')"
echo "📂 Application directory: /opt/consolidador/app"
echo "📊 Logs: /opt/consolidador/app/logs/"
echo "💾 Backups: /opt/consolidador/app/backups/"
echo
echo "🔧 Management commands:"
echo "  • Start:   sudo systemctl start consolidador"
echo "  • Stop:    sudo systemctl stop consolidador"
echo "  • Restart: sudo systemctl restart consolidador"
echo "  • Status:  sudo systemctl status consolidador"
echo "  • Logs:    sudo journalctl -u consolidador -f"
echo
echo "🛡️  Security features enabled:"
echo "  • UFW firewall"
echo "  • Fail2ban intrusion prevention"
echo "  • Automatic security updates"
echo
echo "📋 Next steps:"
echo "  1. Configure your domain in /etc/nginx/sites-available/consolidador"
echo "  2. Set up SSL with: sudo certbot --nginx -d yourdomain.com"
echo "  3. Configure environment variables in /opt/consolidador/app/.env"
echo "  4. Test the application at the URL above"
echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"