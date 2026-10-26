#!/usr/bin/env bash
# ==============================================================================
# GreenLeaf Grocers - Direct Bare-Metal / VPS Deployment Script
# Targets: Ubuntu 22.04 / 24.04 LTS, Debian 12, AWS EC2, DigitalOcean
# ==============================================================================

set -e

echo "=========================================================="
echo "🥬 Starting Direct Production Deployment for GreenLeaf Grocers"
echo "=========================================================="

APP_DIR="/var/www/greenleaf-grocers"
DOMAIN_OR_IP="${1:-_}"

# 1. Update OS & Install Core Tools
echo "[1/6] Updating packages & installing Nginx, Python3, Git..."
sudo apt update -y
sudo apt install -y python3 python3-pip python3-venv nginx git curl

# 2. Setup Application Directory
echo "[2/6] Setting up application folder at $APP_DIR..."
sudo mkdir -p $APP_DIR
sudo chown -R $USER:$USER $APP_DIR

# Copy files from current directory into deployment directory
cp -r . $APP_DIR/
cd $APP_DIR

# 3. Virtual Environment & Dependencies
echo "[3/6] Creating Python virtual environment & installing dependencies..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 4. Initialize Database
echo "[4/6] Initializing and seeding database..."
python seed_data.py

# 5. Create Systemd Service
echo "[5/6] Creating systemd service (/etc/systemd/system/greenleaf.service)..."
sudo bash -c "cat > /etc/systemd/system/greenleaf.service <<EOF
[Unit]
Description=GreenLeaf Grocers Production WSGI (Gunicorn)
After=network.target

[Service]
User=$USER
WorkingDirectory=$APP_DIR
Environment=\"PATH=$APP_DIR/venv/bin\"
Environment=\"FLASK_CONFIG=production\"
Environment=\"PORT=5000\"
ExecStart=$APP_DIR/venv/bin/gunicorn --workers 3 --threads 2 --bind 127.0.0.1:5000 wsgi:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF"

sudo systemctl daemon-reload
sudo systemctl enable greenleaf
sudo systemctl restart greenleaf

# 6. Configure Nginx Reverse Proxy
echo "[6/6] Configuring Nginx reverse proxy..."
sudo bash -c "cat > /etc/nginx/sites-available/greenleaf <<EOF
server {
    listen 80;
    server_name $DOMAIN_OR_IP;

    client_max_body_size 16M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \\\$host;
        proxy_set_header X-Real-IP \\\$remote_addr;
        proxy_set_header X-Forwarded-For \\\$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \\\$scheme;
    }

    location /static/ {
        alias $APP_DIR/app/static/;
        expires 30d;
    }
}
EOF"

sudo ln -sf /etc/nginx/sites-available/greenleaf /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

echo "=========================================================="
echo "🎉 DEPLOYMENT COMPLETE!"
echo "Your GreenLeaf Grocers application is live at: http://$DOMAIN_OR_IP"
echo "Check system service status with: sudo systemctl status greenleaf"
echo "=========================================================="
