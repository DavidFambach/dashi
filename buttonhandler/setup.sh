#!/bin/bash

set -e

# === GET VARIABLES FROM MAIN SCRIPT ===
USER=$1
PROJECT_DIR=$2/buttonhandler

# Function to change the hardware acceleration driver to enable "vcgencmd display_power"
change_hardware_acceleration_driver() {
    echo "Checking and updating hardware acceleration driver..."

    # Check if dtoverlay=vc4-kms-v3d is present
    if grep -q "^dtoverlay=vc4-kms-v3d" /boot/config.txt; then
        echo "dtoverlay=vc4-kms-v3d found, changing it to dtoverlay=vc4-fkms-v3d."
        sudo sed -i 's/dtoverlay=vc4-kms-v3d/dtoverlay=vc4-fkms-v3d/' /boot/config.txt
    else
        echo "dtoverlay=vc4-kms-v3d not found."
    fi

    # Check if dtoverlay=vc4-fkms-v3d is already present
    if ! grep -q "^dtoverlay=vc4-fkms-v3d" /boot/config.txt; then
        echo "dtoverlay=vc4-fkms-v3d not found, adding it."
        echo "dtoverlay=vc4-fkms-v3d" | sudo tee -a /boot/config.txt > /dev/null
    else
        echo "dtoverlay=vc4-fkms-v3d is already present."
    fi

    # Verify the change
    if grep -q "^dtoverlay=vc4-fkms-v3d" /boot/config.txt; then
        echo "Hardware acceleration driver successfully updated."
    else
        echo "Failed to update the hardware acceleration driver."
        exit 1
    fi
}

# Function to reboot the system
reboot_system() {
    echo "Rebooting the system to apply changes..."
    sudo reboot
}

# === SETUP SYSTEMD SERVICE ===
setup_service() {
    echo "Setting up systemd service..."
    sed -i \
      -e "s|{{PROJECT_DIR}}|$PROJECT_DIR|g" \
      -e "s|{{USER}}|$USER|g" \
      dashi-buttonhandler.service
    sudo mv "$PROJECT_DIR"/dashi-buttonhandler.service /etc/systemd/system/dashi-buttonhandler.service
    sudo systemctl daemon-reload
    sudo systemctl enable dashi-buttonhandler.service
    sudo systemctl start dashi-buttonhandler.service
}

# Main installation function
install() {
    echo "Starting installation process..."

    # Call the individual functions in the order of execution
    change_hardware_acceleration_driver
    setup_service
    reboot_system
}

# Execute the main installation function
install
