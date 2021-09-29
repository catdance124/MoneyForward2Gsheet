# MoneyForward2Gsheet
Downloading asset trends📈 from MoneyForward, and exporting them to google spreadsheet, in python.

## env
*Accessing MoneyForward from Japan*
```
OS: Windows / CentOS7(CLI)
Python (win)3.8.5, (centos)3.6.8
```
```
# for download
pip install selenium, pandas
# for export
pip gspread oauth2client
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

[SPREAD_SHEET]
Key = <spreadsheet key got from URL>
Worksheet_name = <any sheet name>
; Worksheet_name = 資産推移データ(自動入力)
```

### google spreadsheet R/W
enable API, and allow client to edit your sheet.  
[reference](https://qiita.com/164kondo/items/eec4d1d8fd7648217935)  

Place the obtained json file as src/client_secret.json .


## run
```
# cd src
# python mf2gs.py

## for csv download only
# python download_history.py
## for csv export to sheet only
# python export_gspread.py
```

## Appendix
### cron settings
```
# crontab -e
0 9 * * * export DISPLAY=localhost:1.0; python3 /home/opc/MoneyForward2Gsheet/src/mf2gs.py
10 9 * * * ps aux | grep chromedriver | grep -v grep | awk '{ print "kill -9", $2 }' | sh
10 9 * * * ps aux | grep "Google Chrome" | grep -v grep | awk '{ print "kill -9", $2 }' | sh
10 9 * * * ps aux | grep "Google Helper" | grep -v grep | awk '{ print "kill -9", $2 }' | sh
```

### result
Asset transition data written to a spreadsheet. ( Of course, the numbers are dummy XD )  
![image](https://user-images.githubusercontent.com/37448236/135253334-587f63aa-f8d9-4039-b945-03c50d2eea14.png)

With this data, you can create any graph you like.  
As shown below. [reference](https://fire-hiko.com/moneyfoward-graph-tool/)
![IMG-9422](https://user-images.githubusercontent.com/37448236/135253595-f9645898-f5da-4cad-8bb1-8c9af2aa23cb.PNG)  
![IMG-9423](https://user-images.githubusercontent.com/37448236/135253598-736f032e-5f19-4fb4-9d30-0e669d2eb7b7.PNG)  
