# MoneyForward2Gsheet
Downloading asset trends📈 from `マネーフォワード for 住信SBIネット銀行`, and exporting them to google spreadsheet, in python.

Scraping is done by [mf-sbi-client](https://github.com/catdance124/mf-sbi-client) (httpx + BeautifulSoup) — no browser, no docker required.

## env
- [uv](https://docs.astral.sh/uv/) (manages Python >= 3.12 automatically)

## layout
```
MoneyForward2Gsheet/
├── .env                 # credentials (gitignored, see .env.example)
├── config.ini           # spreadsheet & asset settings
├── client_secret.json   # google service account key
├── csv/                 # generated csv (gitignored)
├── log/                 # log file (gitignored)
└── src/mf2gs/           # package: config / download / aggregate / export / cli
```

## setting
### create account
https://ssnb.x.moneyforward.com/

### fill in `.env`
Copy `.env.example` to `.env` and fill in your credentials (JSON arrays, multi-account supported):
```sh
# case of single account
MF_SBI_EMAILS='["<REGISTERED EMAIL>"]'
MF_SBI_PASSWORDS='["<REGISTERED PASSWORD>"]'

# case of multi account
MF_SBI_EMAILS='["<EMAIL 1>", "<EMAIL 2>", "<EMAIL 3>"]'
MF_SBI_PASSWORDS='["<PASSWORD 1>", "<PASSWORD 2>", "<PASSWORD 3>"]'
```

### fill in `config.ini`
```ini
[SPREAD_SHEET]
Key = <SPREADSHEET KEY got from URL>
```

### google spreadsheet R/W
enable API, and allow client to edit your sheet.  
[reference](https://qiita.com/164kondo/items/eec4d1d8fd7648217935)  

Place the obtained json file as `client_secret.json` (repository root).


## run
Run from the repository root:
```shell
$ pwd
~/MoneyForward2Gsheet
$ uv sync
$ uv run mf2gs             # download + export
$ uv run mf2gs download    # download only
$ uv run mf2gs export      # export only
```

For periodic execution, register it in cron. e.g.
```cron
0 6 * * * cd ~/MoneyForward2Gsheet && ~/.local/bin/uv run mf2gs
```

## Appendix
### result
Asset transition data written to a spreadsheet. ( Of course, the numbers are dummy XD )  

![IMG_3395](https://user-images.githubusercontent.com/37448236/204326636-1e3d3669-0008-4d86-a123-d7f80c799b01.PNG)

With this data, you can create any graph you like.  
As shown below. [reference](https://fire-hiko.com/moneyfoward-graph-tool/)
![IMG_3396](https://user-images.githubusercontent.com/37448236/204327307-909cf195-b080-4356-afd4-55c06e87cd7a.PNG)

![IMG_3394](https://user-images.githubusercontent.com/37448236/204326618-60d07ff5-4d56-4548-b5b1-499cd03939de.PNG)
