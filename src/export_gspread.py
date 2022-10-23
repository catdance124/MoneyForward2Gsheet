import configparser
import csv
from pathlib import Path
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import numpy as np
from my_logging import get_my_logger
logger = get_my_logger(__name__)


root_csv_dir = Path('../csv')
portfolio_csv_dir = root_csv_dir / 'portfolio'

def connect_gspread(json_path, spreadsheet_key):
    scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(json_path, scope)
    gc = gspread.authorize(credentials)
    workbook = gc.open_by_key(spreadsheet_key)
    return workbook

def update_sheet(workbook, worksheet_name, csv_path):
    if not worksheet_name in [worksheet.title for worksheet in workbook.worksheets()]:
        workbook.add_worksheet(title=worksheet_name, rows=50, cols=50)
    ws = workbook.worksheet(worksheet_name)
    ws.clear()
    workbook.values_update(
        worksheet_name,
        params={'valueInputOption': 'USER_ENTERED'},
        body={'values': list(csv.reader(open(csv_path, encoding='shift-jis')))}
    )

def calc_profit_and_loss(assets):
    df_all_org = pd.read_csv(root_csv_dir / "all.csv", encoding="shift-jis", sep=',')
    portfolio_all_csv_path = portfolio_csv_dir / "portfolio_all.csv"
    if portfolio_all_csv_path.exists():
        df_all_with_profit_and_loss = pd.read_csv(portfolio_all_csv_path, encoding="shift-jis", sep=',')
    else:
        df_all_with_profit_and_loss = df_all_org
    df_all_with_profit_and_loss = pd.merge(df_all_org, df_all_with_profit_and_loss, how='left')
    df_all_with_profit_and_loss.drop_duplicates(subset='日付', inplace=True)
    df_all_with_profit_and_loss.set_index('日付', inplace=True)
    portfolios = [{asset['column_name']: portfolio_csv_dir / f"{asset['id']}.csv"} for asset in assets if asset['column_name'] != '']
    for portfolio in portfolios:
        column_name, portfolio_csv_path = list(portfolio.items())[0]
        df = pd.read_csv(portfolio_csv_path, encoding="shift-jis", sep=',')
        df = df.dropna(subset=['評価損益'])
        df['評価損益'] = df['評価損益'].apply(lambda x: x.strip('円') if '円' in x else x)
        df['評価損益'] = df['評価損益'].str.replace(',','').astype(np.int)
        profit_and_loss = df['評価損益'].sum()
        if not column_name in df_all_with_profit_and_loss.columns:
            df_all_with_profit_and_loss[column_name] = 0
        df_all_with_profit_and_loss.at[df_all_with_profit_and_loss.index[0], column_name] = profit_and_loss
    df_all_with_profit_and_loss.to_csv(portfolio_csv_dir / 'portfolio_all.csv', encoding="shift-jis")
    

def main():
    config_ini = configparser.ConfigParser()
    config_ini.read('config.ini', encoding='utf-8')
    spreadsheet_key = config_ini.get('SPREAD_SHEET', 'Key')
    assets = [dict(config_ini.items(section)) for section in config_ini.sections() if "asset_" in section]
    
    calc_profit_and_loss(assets)

    assets.append({'id': 'portfolio_all', 'sheet_name': config_ini.get('SPREAD_SHEET', 'Worksheet_name')})
    workbook = connect_gspread(json_path="client_secret.json", spreadsheet_key=spreadsheet_key)
    for asset in assets:
        update_sheet(workbook, asset['sheet_name'], portfolio_csv_dir / f"{asset['id']}.csv")
        logger.info(asset['sheet_name'], portfolio_csv_dir / f"{asset['id']}.csv")


if __name__ == "__main__":
    main()