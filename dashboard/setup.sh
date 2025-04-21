#!/bin/bash

set -e

# === GET VARIABLES FROM MAIN SCRIPT ===
USER=$1
PROJECT_DIR=$2/dashboard

# === CREATE PYTHON VIRTUAL ENVIRONMENT ===
python3 -m venv "$PROJECT_DIR"/venv

# === INSTALL PYTHON DEPENDENCIES ===
echo "Installing Python dependencies..."
"$PROJECT_DIR"/venv/bin/pip install -r "$PROJECT_DIR"/requirements.txt

# === SETUP SYSTEMD SERVICE ===
echo "Setting up systemd service..."
sed -i \
  -e "s|{{PROJECT_DIR}}|$PROJECT_DIR|g" \
  -e "s|{{USER}}|$USER|g" \
  dashi-dashboard.service
sudo mv "$PROJECT_DIR"/dashi-dashboard.service /etc/systemd/system/dashi-dashboard.service
sudo systemctl daemon-reload
sudo systemctl enable dashi-dashboard.service
sudo systemctl start dashi-dashboard.service
