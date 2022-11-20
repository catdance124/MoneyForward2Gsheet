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
![image](https://user-images.githubusercontent.com/37448236/135253334-587f63aa-f8d9-4039-b945-03c50d2eea14.png)

With this data, you can create any graph you like.  
As shown below. [reference](https://fire-hiko.com/moneyfoward-graph-tool/)
![IMG-9422](https://user-images.githubusercontent.com/37448236/135253595-f9645898-f5da-4cad-8bb1-8c9af2aa23cb.PNG)  
