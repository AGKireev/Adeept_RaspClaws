# Adeept_RaspClaws

# How to set env
cd /home/USERNAME
python3 -m venv adeept_env
source adeept_env/bin/activate
pip install -r requirements.txt
deactivate
sudo nano /etc/systemd/system/adeept_webserver.service
-----------------
[Unit]
Description=Adeept RaspClaws Web Server
After=network.target

[Service]
User=root
WorkingDirectory=/home/USERNAME/Adeept_RaspClaws/server
ExecStart=/home/USERNAME/adeept_env/bin/python3 /home/USERNAME/Adeept_RaspClaws/server/webServer.py

[Install]
WantedBy=multi-user.target
-----------------
Save the file
sudo systemctl daemon-reload
sudo systemctl restart adeept_webserver.service
sudo systemctl status adeept_webserver.service

# How to set/reset service

# How to Fix led errors for Raspberry 5
# @from https://github.com/jgarff/rpi_ws281x/issues/528
# @from https://github.com/rpi-ws281x/rpi-ws281x-python/releases
sudo apt update
sudo apt install linux-headers-$(uname -r) device-tree-compiler raspi-utils
git clone --branch pi5 https://github.com/jgarff/rpi_ws281x.git
cd rpi_ws281x
cd rp1_ws281x_pwm
make
./dts.sh
sudo insmod ./rp1_ws281x_pwm.ko pwm_channel=0
sudo dtoverlay -d . rp1_ws281x_pwm
sudo pinctrl set 12 a0 pn
sudo apt install cmake -y
cmake --version
cmake .
make
pip uninstall rpi_ws281x -y
pip install https://github.com/rpi-ws281x/rpi-ws281x-python/releases/download/pi5-beta2/rpi_ws281x-6.0.0-cp311-cp311-linux_aarch64.whl
pip show rpi_ws281x
sudo ./test