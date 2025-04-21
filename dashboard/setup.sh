#!/bin/bash

set -e

# === GET VARIABLES FROM MAIN SCRIPT ===
USER=$1
PROJECT_DIR=$2
UPDATE_SCRIPT="$PROJECT_DIR/update.sh"

# === CREATE PYTHON VIRTUAL ENVIRONMENT ===
python3 -m venv venv

# === INSTALL PYTHON DEPENDENCIES ===
echo "Installing Python dependencies..."
./venv/bin/pip install -r "$PROJECT_DIR/dashboard/requirements.txt"

# === SETUP SYSTEMD SERVICE ===
echo "Setting up systemd service..."
sudo mv dashi-dashboard.service /etc/systemd/system/dashi-dashboard.service
sudo systemctl daemon-reload
sudo systemctl enable dashi-dashboard.service
sudo systemctl start dashi-dashboard.service
