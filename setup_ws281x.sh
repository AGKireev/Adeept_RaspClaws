#!/bin/bash
# Setup script for WS281x lights on Raspberry Pi 5

echo "Starting WS281x setup script..."

# Step 1: Add the kernel module to /etc/modules
echo "Adding rp1_ws281x_pwm module to /etc/modules..."
if ! grep -q "rp1_ws281x_pwm" /etc/modules; then
    echo "rp1_ws281x_pwm" | sudo tee -a /etc/modules
else
    echo "Kernel module already in /etc/modules."
fi

# Step 2: Create a modprobe configuration file for module parameters
echo "Creating modprobe configuration for rp1_ws281x_pwm..."
sudo bash -c 'cat > /etc/modprobe.d/rp1_ws281x_pwm.conf <<EOF
options rp1_ws281x_pwm pwm_channel=0
EOF'

# Step 3: Add the overlay to /boot/firmware/config.txt
echo "Adding rp1_ws281x_pwm overlay to /boot/firmware/config.txt..."
if ! grep -q "dtoverlay=rp1_ws281x_pwm" /boot/firmware/config.txt; then
    sudo bash -c 'echo "dtoverlay=rp1_ws281x_pwm" >> /boot/firmware/config.txt'
else
    echo "Overlay already in /boot/firmware/config.txt."
fi

# Step 4: Add the pin configuration to /etc/rc.local
echo "Configuring GPIO pin setup in /etc/rc.local..."
if ! grep -q "pinctrl set 12 a0 pn" /etc/rc.local; then
    sudo sed -i -e '$i \pinctrl set 12 a0 pn\n' /etc/rc.local
else
    echo "Pin configuration already in /etc/rc.local."
fi

# Step 5: Ensure /etc/rc.local exists and is executable
if [ ! -f /etc/rc.local ]; then
    echo "Creating /etc/rc.local..."
    sudo bash -c 'cat > /etc/rc.local <<EOF
#!/bin/bash
pinctrl set 12 a0 pn
exit 0
EOF'
    sudo chmod +x /etc/rc.local
fi

# Finish
echo "Setup complete. Please reboot your Raspberry Pi to apply changes."
