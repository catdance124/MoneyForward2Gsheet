# download_asset_trends_from_MoneyForward
Downloading asset trends from MoneyForward  
to try to visualize asset trends retrieved from MoneyForward in python.

## env
*Accessing MoneyForward from Japan*
```
OS: Windows / CentOS7(CLI)
Python (win)3.8.5, (centos)3.6.8
selenium
pandas
ChromeDriver: (win)93.0.4577.63, (centos)94.0.4606.61
```

### Install py lib
```
pip install selenium, pandas
```

### Install web driver(Windows)
Download the binary from https://sites.google.com/chromium.org/driver/  
and install it to bin/ .

### Install web driver(CentOS)
chrome install  
[reference](https://qiita.com/mindwood/items/245adeb6da18999bbfc4)  
```
# vim /etc/yum.repos.d/google.chrome.repo
[google-chrome]
name=google-chrome
baseurl=http://dl.google.com/linux/chrome/rpm/stable/$basearch
enabled=1
gpgcheck=1
gpgkey=https://dl-ssl.google.com/linux/linux_signing_key.pub
```
```
# yum update
# yum -y install google-chrome-stable
# google-chrome --version
Google Chrome 94.0.4606.61
# yum -y install ipa-gothic-fonts ipa-mincho-fonts ipa-pgothic-fonts ipa-pmincho-fonts
# google-chrome --headless --no-sandbox --dump-dom https://www.google.com/
```
web driver install  
```
# cd /usr/local/bin
# wget https://chromedriver.storage.googleapis.com/94.0.4606.61/chromedriver_linux64.zip
# unzip chromedriver_linux64.zip
# chmod 755 chromedriver
# rm chromedriver_linux64.zip 
```
virtual display install  
[reference](https://qiita.com/kotanbo/items/093fc71b71ee5f20baf0#xvfb)
```
# yum install xorg-x11-server-Xvfb
```
```
# vim /usr/lib/systemd/system/Xvfb.service
[Unit]
Description=Virtual Framebuffer X server for X Version 11

[Service]
Type=simple
EnvironmentFile=-/etc/sysconfig/Xvfb
ExecStart=/usr/bin/Xvfb $OPTION
ExecReload=/bin/kill -HUP ${MAINPID}

[Install]
WantedBy=multi-user.target
```
```
# vim /etc/sysconfig/Xvfb
# Xvfb Enviroment File
OPTION=":1 -screen 0 1366x768x24"
```
```
# systemctl enable Xvfb
# systemctl start Xvfb
```
```
# export DISPLAY=localhost:1.0;
```

## setting
fill in src/config.ini
```
[MONEYFORWARD]
Email = <registered email>
Password = <registered password>

[CHROME_DRIVER]
Path = <installed path>
; Path = ../bin/chromedriver.exe
; Path = /usr/local/bin/chromedriver
```

## run
```
# cd src
# python download_history.py
```

## Appendix: cron settings
```
# crontab -e
0 9 * * * export DISPLAY=localhost:1.0; python3 /home/opc/download_asset_trends_from_MoneyForward/src/download_history.py
```