# MoneyForward2Gsheet
Downloading asset trends📈 from MoneyForward, and exporting them to google spreadsheet, in python.

## env
*Accessing MoneyForward from Japan*
```
OS: Windows10
Python: 3.8.5
```
```
OS: CentOS7(CLI)
Python: 3.6.8
```

### Install
#### some python package install (Windows&CentOS)
```
# for download
pip3 install selenium, pandas, webdriver-manager
# for export
pip3 gspread oauth2client
```
`webdriver-manager` is required to use the chromedriver that matches the version of google-chrome.

#### chrome install (CentOS)
[reference](https://qiita.com/mindwood/items/245adeb6da18999bbfc4)  
```
# vim /etc/yum.repos.d/google.chrome.repo
```
```
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
#### virtual display install (CentOS)
[reference](https://gist.github.com/ypandit/f4fe751bcbf3ee6a32ca)
```
# yum install xorg-x11-server-Xvfb
```
```
# vim /etc/systemd/system/Xvfb.service
```
```config
[Unit]
Description=X Virtual Frame Buffer Service
After=network.target

[Service]
ExecStart=/usr/bin/Xvfb :99 -screen 0 1024x768x24

[Install]
WantedBy=multi-user.target
```
```
# systemctl enable Xvfb.service
# systemctl start Xvfb.service
```
Export the virtual display created(:99) as the `DISPLAY` environment variable.  
```
# export DISPLAY=localhost:99
```

## setting
fill in `src/config.ini`
```
[MONEYFORWARD]
Email = <registered email>
Password = <registered password>

[SPREAD_SHEET]
Key = <spreadsheet key got from URL>
```

### google spreadsheet R/W
enable API, and allow client to edit your sheet.  
[reference](https://qiita.com/164kondo/items/eec4d1d8fd7648217935)  

Place the obtained json file as `src/client_secret.json` .


## run
```
# cd src
# export DISPLAY=localhost:99; python3 mf2gs.py

## for csv download only
# export DISPLAY=localhost:99; python3 download_history.py
## for csv export to sheet only
# export DISPLAY=localhost:99; python3 export_gspread.py
```

## Appendix
### cron settings
After running, kill the remaining chrome processes.
```
# crontab -e
0 * * * * export DISPLAY=localhost:99; export LANG=ja_JP.UTF-8; cd /home/opc/MoneyForward2Gsheet/src; date >> log; python3 mf2gs.py >> log 2>&1;
```

### result
Asset transition data written to a spreadsheet. ( Of course, the numbers are dummy XD )  
![image](https://user-images.githubusercontent.com/37448236/135253334-587f63aa-f8d9-4039-b945-03c50d2eea14.png)

With this data, you can create any graph you like.  
As shown below. [reference](https://fire-hiko.com/moneyfoward-graph-tool/)
![IMG-9422](https://user-images.githubusercontent.com/37448236/135253595-f9645898-f5da-4cad-8bb1-8c9af2aa23cb.PNG)  
![IMG-9423](https://user-images.githubusercontent.com/37448236/135253598-736f032e-5f19-4fb4-9d30-0e669d2eb7b7.PNG)  
