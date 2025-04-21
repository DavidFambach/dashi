#!/bin/bash

set -e

# === CONFIGURATION ===
KIOSK_URL="https://127.0.0.1/dashboard/0"
DEFAULT_USER="dashi"
CURRENT_USER=$(logname)
LOGFILE="/var/log/kiosk-setup.log"

# === COLORS FOR LOGGING ===
GREEN="\033[1;32m"
YELLOW="\033[1;33m"
BLUE="\033[1;34m"
RED="\033[1;31m"
RESET="\033[0m"

# === TIMESTAMPED LOGGING ===
timestamp() {
  date +"%Y-%m-%d %H:%M:%S"
											 
}

logfile() {
  while IFS= read -r line; do
    echo "$(timestamp) | $line" >> "$LOGFILE"
  done
}

log()    { echo -e "${GREEN}[✔]${RESET} $1"; echo "[✔] $(timestamp) $1" >> "$LOGFILE"; }
warn()   { echo -e "${YELLOW}[!]${RESET} $1"; echo "[!] $(timestamp) $1" >> "$LOGFILE"; }
info()   { echo -e "${BLUE}[i]${RESET} $1"; echo "[i] $(timestamp) $1" >> "$LOGFILE"; }
error()  { echo -e "${RED}[✖]${RESET} $1"; echo "[✖] $(timestamp) $1" >> "$LOGFILE"; }

info "🔧 Raspberry Pi Kiosk Setup"
echo "$(timestamp) ===== Raspberry Pi Kiosk Setup gestartet =====" >> "$LOGFILE"

# === USER SETUP ===
echo ""
info "Do you want to use the current user \"$CURRENT_USER\" for the kiosk setup?"
echo "Press [Y/j/yes] to use \"$CURRENT_USER\", or press [Enter] (or wait 5 seconds) to create and use user \"$DEFAULT_USER\"."
read -t 5 -p "[Y/j/yes, default: no] " USE_CURRENT

USE_CURRENT=$(echo "$USE_CURRENT" | tr '[:upper:]' '[:lower:]')

if [[ "$USE_CURRENT" =~ ^(y|j|yes)$ ]]; then
  USER="$CURRENT_USER"
  log "Using current user: $USER"
else
  USER="$DEFAULT_USER"
  info "Creating user \"$USER\"..."
  if ! id "$USER" &>/dev/null; then
    sudo adduser --disabled-password --gecos "" "$USER" 2>&1 | logfile
    sudo usermod -aG sudo "$USER" 2>&1 | logfile
    log "User \"$USER\" created and added to sudo group"
  else
    warn "User \"$USER\" already exists, reusing."
  fi
fi

# === NETWORK CHECK ===
info "🌐 Checking internet connection..."
if ! ping -c 2 8.8.8.8 &>/dev/null; then
  error "No internet connection – cannot continue!"
  exit 1
fi

# === SYSTEM UPDATE ===
info "📦 Updating system packages..."
sudo apt-get update -qq 2>&1 | logfile
sudo apt-get upgrade -y 2>&1 | logfile

# === DEPENDENCY INSTALLATION ===
info "📥 Installing X server and Chromium browser..."
if ! sudo apt-get install --no-install-recommends -y \
  xserver-xorg-video-all \
  xserver-xorg-input-all \
  xserver-xorg-core \
  xinit \
  x11-xserver-utils \
  chromium-browser \
  unclutter 2>&1 | logfile; then
  error "Package installation failed – check $LOGFILE"
  exit 1
fi
log "Packages installed"

# === ENABLE AUTOLOGIN ===
info "🔐 Enabling autologin for user \"$USER\" on tty1..."
sudo mkdir -p /etc/systemd/system/getty@tty1.service.d
cat <<EOF | sudo tee /etc/systemd/system/getty@tty1.service.d/autologin.conf > /dev/null
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin $USER --noclear %I \$TERM
EOF

sudo systemctl daemon-reexec
sudo systemctl restart getty@tty1
log "Autologin enabled for user \"$USER\""

# === .bash_profile SETUP ===
BASH_PROFILE="/home/$USER/.bash_profile"
info "📝 Configuring .bash_profile to start X on tty1..."
													   
sudo -u "$USER" bash -c "echo 'if [ -z \"\$DISPLAY\" ] && [ \"\$(tty)\" = \"/dev/tty1\" ]; then' >> \"$BASH_PROFILE\""
sudo -u "$USER" bash -c "echo '  startx' >> \"$BASH_PROFILE\""
sudo -u "$USER" bash -c "echo 'fi' >> \"$BASH_PROFILE\""
log ".bash_profile configured"

# === .xinitrc SETUP ===
XINITRC="/home/$USER/.xinitrc"
info "🖥️ Creating .xinitrc to launch Chromium in kiosk mode..."
sudo -u "$USER" bash -c "cat <<EOF > $XINITRC
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
log ".xinitrc created and configured"

# === DISABLE HDMI OVERSCAN ===
info "🖼️ Disabling HDMI overscan..."
sudo sed -i '/^#disable_overscan=1/s/^#//' /boot/config.txt || true

# === CHROMIUM MEMORY PATCH ===
info "🧠 Checking if Chromium needs patching..."
CHROMIUM_LAUNCHER="$(command -v chromium-browser || command -v chromium)"

if [[ ! -x "$CHROMIUM_LAUNCHER" ]]; then
  error "Chromium launcher not found"
else
  TOTAL_RAM_KB=$(awk '/^MemTotal:/ { print $2 }' /proc/meminfo)

  CHROMIUM_BLOCK_LINES=(
    'if [ $want_memcheck -eq 1 ]; then'
    '  memkb=$(awk '\''/^MemTotal/{print $2; exit}'\'' /proc/meminfo)'
    '  if [ $memkb -le 524288 ]; then'
    '    if ! display_qstn "$lowmem" "$lowmemok"; then'
    '            exit 1'
    '    fi'
    '  fi'
    'fi'
  )

  # Function to locate memory check block in script
  match_block() {
    local file="$1"
    local -n block="$2"
    mapfile -t lines < "$file"

    for ((i = 0; i <= ${#lines[@]} - ${#block[@]}; i++)); do
      local match=true
      for ((j = 0; j < ${#block[@]}; j++)); do
        local file_line="$(echo "${lines[i + j]}" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
        local block_line="$(echo "${block[j]}"     | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
        if [[ "$file_line" != "$block_line" ]]; then
          match=false
          break
        fi
      done
      if $match; then
        echo "$i"
        return 0
      fi
    done
    return 1
  }

  if [[ "$TOTAL_RAM_KB" -le 524288 ]]; then
    info "⚙️ System has ≤1GB RAM — checking Chromium memory check..."
    if grep -q "memcheck" "$CHROMIUM_LAUNCHER"; then
      BLOCK_START_LINE=$(match_block "$CHROMIUM_LAUNCHER" CHROMIUM_BLOCK_LINES)
      if [[ $? -eq 0 ]]; then
        log "Chromium memory check block found at line $((BLOCK_START_LINE + 1))"
        sudo cp "$CHROMIUM_LAUNCHER" "${CHROMIUM_LAUNCHER}.bak"
        for ((k = 0; k < ${#CHROMIUM_BLOCK_LINES[@]}; k++)); do
          sudo sed -i "$((BLOCK_START_LINE + k + 1))s/^/#/" "$CHROMIUM_LAUNCHER"
        done
        log "Chromium launcher patched successfully (backup created)"
      else
        warn "Expected Chromium block not found or already modified"
      fi
    else
      info "Chromium launcher does not contain memory check logic"
    fi
  else
    info "🧠 System has more than 1GB RAM, no Chromium patch needed"
  fi
	
									   
fi


# === INSTALL WEBSERVER ===
PATH="/home/$USER/dashi/"
mv ./dashboard $PATH/dashboard
./dashboard/setup.sh "$USER" "$PATH"


# === FINAL MESSAGE ===
echo ""
log "Kiosk setup complete for user \"$USER\"."
echo "🔄 Please reboot the system to apply all changes."

read -p "Reboot now? (y/n) " REBOOT
REBOOT=$(echo "$REBOOT" | tr '[:upper:]' '[:lower:]')
if [[ "$REBOOT" =~ ^(y|j|yes)$ ]]; then
  sudo reboot
fi
