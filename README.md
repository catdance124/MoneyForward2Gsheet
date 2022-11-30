# MoneyForward2Gsheet
Downloading asset trends📈 from MoneyForward, and exporting them to google spreadsheet, in python.

## env
- docker

## setting
fill in `src/config.ini`
```ini
# case of single account
[MONEYFORWARD]
Email = [
    "<REGISTERED EMAIL>"
]
Password = [
    "<REGISTERED PASSWORD>"
]

# case of multi account
[MONEYFORWARD]
Email = [
    "<REGISTERED EMAIL 1>",
    "<REGISTERED EMAIL 2>",
    "<REGISTERED EMAIL 3>"
]
Password = [
    "<REGISTERED PASSWORD 1>",
    "<REGISTERED PASSWORD 2>",
    "<REGISTERED PASSWORD 3>"
]


[SPREAD_SHEET]
Key = <SPREADSHEET KEY got from URL>
```

### google spreadsheet R/W
enable API, and allow client to edit your sheet.  
[reference](https://qiita.com/164kondo/items/eec4d1d8fd7648217935)  

Place the obtained json file as `src/client_secret.json` .


## run
```shell
$ pwd
~/MoneyForward2Gsheet
$ bash make_env.sh
$ docker-compose build
$ docker-compose up -d
```

## Appendix
### result
Asset transition data written to a spreadsheet. ( Of course, the numbers are dummy XD )  

![IMG_3395](https://user-images.githubusercontent.com/37448236/204326636-1e3d3669-0008-4d86-a123-d7f80c799b01.PNG)

With this data, you can create any graph you like.  
As shown below. [reference](https://fire-hiko.com/moneyfoward-graph-tool/)
![IMG_3396](https://user-images.githubusercontent.com/37448236/204327307-909cf195-b080-4356-afd4-55c06e87cd7a.PNG)

![IMG_3394](https://user-images.githubusercontent.com/37448236/204326618-60d07ff5-4d56-4548-b5b1-499cd03939de.PNG)
