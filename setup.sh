#!/bin/bash

set -e

# === CONFIG ===
KIOSK_URL="https://time.is"
DEFAULT_USER="dashi"

# === COLORS ===
GREEN="\033[1;32m"
YELLOW="\033[1;33m"
BLUE="\033[1;34m"
RED="\033[1;31m"
RESET="\033[0m"

# === LOGGING HELPERS ===
log()    { echo -e "${GREEN}[✔]${RESET} $1"; }
warn()   { echo -e "${YELLOW}[!]${RESET} $1"; }
info()   { echo -e "${BLUE}[i]${RESET} $1"; }
error()  { echo -e "${RED}[✖]${RESET} $1"; }

# === MAIN SETUP ===
info "Starting Raspberry Pi Kiosk Setup..."

CURRENT_USER=$(logname)

# --- User selection ---
echo ""
info "Detected current user: $CURRENT_USER"
read -t 5 -p "Use current user for kiosk setup? [Y/j/yes] (Default = create \"$DEFAULT_USER\"): " USE_CURRENT
USE_CURRENT=$(echo "$USE_CURRENT" | tr '[:upper:]' '[:lower:]')

if [[ "$USE_CURRENT" =~ ^(y|j|yes)$ ]]; then
  USER="$CURRENT_USER"
  log "Using current user: $USER"
else
  USER="$DEFAULT_USER"
  info "Creating user: $USER"
  if ! id "$USER" &>/dev/null; then
    sudo adduser --disabled-password --gecos "" "$USER"
    sudo usermod -aG sudo "$USER"
    log "User \"$USER\" created successfully"
  else
    warn "User \"$USER\" already exists. Proceeding with existing user."
  fi
fi

# --- System update ---
info "Updating system packages..."
sudo apt-get update -qq
sudo apt-get upgrade -y

# --- Install dependencies ---
info "Installing X and Chromium browser..."
sudo apt-get install --no-install-recommends -y \
  xserver-xorg-video-all \
  xserver-xorg-input-all \
  xserver-xorg-core \
  xinit \
  x11-xserver-utils \
  chromium-browser \
  unclutter

# --- Autologin configuration ---
info "Enabling autologin for user \"$USER\" on tty1..."
sudo mkdir -p /etc/systemd/system/getty@tty1.service.d
sudo tee /etc/systemd/system/getty@tty1.service.d/autologin.conf > /dev/null <<EOF
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin $USER --noclear %I \$TERM
EOF

sudo systemctl daemon-reexec
sudo systemctl restart getty@tty1

# --- .bash_profile setup ---
BASH_PROFILE="/home/$USER/.bash_profile"
info "Configuring .bash_profile to auto-launch X on tty1..."
sudo -u "$USER" bash -c "cat <<EOF >> \"$BASH_PROFILE\"
if [ -z \"\$DISPLAY\" ] && [ \"\$(tty)\" = \"/dev/tty1\" ]; then
  startx
fi
EOF"

# --- .xinitrc setup ---
XINITRC="/home/$USER/.xinitrc"
info "Creating .xinitrc to launch Chromium in kiosk mode..."
sudo -u "$USER" bash -c "cat <<EOF > \"$XINITRC\"
#!/usr/bin/env sh
xset -dpms
xset s off
xset s noblank
unclutter &
chromium-browser \"$KIOSK_URL\" \\
  --window-position=0,0 \\
  --start-fullscreen \\
  --kiosk \\
  --incognito \\
  --noerrdialogs \\
  --disable-translate \\
  --no-first-run \\
  --disable-infobars \\
  --disable-features=TranslateUI \\
  --disk-cache-dir=/dev/null \\
  --overscroll-history-navigation=0 \\
  --disable-pinch
EOF"

sudo chmod +x "$XINITRC"
sudo chown "$USER:$USER" "$XINITRC"

# --- Disable overscan ---
info "Disabling HDMI overscan..."
sudo sed -i '/^#disable_overscan=1/s/^#//' /boot/config.txt || true

# --- Chromium memory patch (for devices with low RAM) ---
CHROMIUM_LAUNCHER="$(command -v chromium-browser || command -v chromium)"

if [[ -x "$CHROMIUM_LAUNCHER" ]]; then
  TOTAL_RAM_KB=$(awk '/^MemTotal:/ { print $2 }' /proc/meminfo)
  if [[ "$TOTAL_RAM_KB" -le 524288 ]]; then
    info "Low RAM system detected. Checking Chromium memory check block..."
    if grep -q "memcheck" "$CHROMIUM_LAUNCHER"; then
      log "Patching Chromium memory check..."
      sudo cp "$CHROMIUM_LAUNCHER" "${CHROMIUM_LAUNCHER}.bak"
      sudo sed -i '/memcheck/,/fi/s/^/#/' "$CHROMIUM_LAUNCHER"
      log "Chromium patched successfully (backup saved)"
    else
      warn "Memory check logic not found in Chromium script"
    fi
  else
    info "Sufficient memory detected. No Chromium patch needed."
  fi
else
  error "Chromium not found on system!"
fi

# --- Final prompt ---
log "Kiosk setup complete for user \"$USER\"."
read -p "Reboot now to apply changes? (y/n): " REBOOT
REBOOT=$(echo "$REBOOT" | tr '[:upper:]' '[:lower:]')
if [[ "$REBOOT" =~ ^(y|j|yes)$ ]]; then
  sudo reboot
fi
