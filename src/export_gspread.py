import configparser
import csv
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import numpy as np


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

def calc_profit_and_loss():
    csv_path = "../csv/all.csv"
    df_all_org = pd.read_csv(csv_path, encoding="shift-jis", sep=',')
    csv_path = "../csv/portfolio/portfolio_all.csv"
    df_all_with_profit_and_loss = pd.read_csv(csv_path, encoding="shift-jis", sep=',')
    df_all_with_profit_and_loss = pd.merge(df_all_org, df_all_with_profit_and_loss, how='left')
    df_all_with_profit_and_loss.drop_duplicates(subset='日付', inplace=True)
    df_all_with_profit_and_loss.set_index('日付', inplace=True)
    portfolio  = {'損益_投資信託':'../csv/portfolio/portfolio_det_mf.csv',
                '損益_年金':'../csv/portfolio/portfolio_det_pns.csv',
                '損益_株式（現物）':'../csv/portfolio/portfolio_det_eq.csv'}
    for name, csv_path in portfolio.items():
        df = pd.read_csv(csv_path, encoding="shift-jis", sep=',')
        df = df.dropna(subset=['評価損益'])
        df['評価損益'] = df['評価損益'].apply(lambda x: x.strip('円') if '円' in x else x)
        df['評価損益'] = df['評価損益'].str.replace(',','').astype(np.int)
        profit_and_loss = df['評価損益'].sum()
        if not name in df_all_with_profit_and_loss.columns:
            df_all_with_profit_and_loss[name] = 0
        else:
            df_all_with_profit_and_loss.at[df_all_with_profit_and_loss.index[0], name] = profit_and_loss
    df_all_with_profit_and_loss.to_csv('../csv/portfolio/portfolio_all.csv', encoding="shift-jis")
    

def main():
    config_ini = configparser.ConfigParser()
    config_ini.read('config.ini', encoding='utf-8')
    spreadsheet_key = config_ini.get('SPREAD_SHEET', 'Key')
    calc_profit_and_loss()
    
    workbook = connect_gspread(json_path="client_secret.json", spreadsheet_key=spreadsheet_key)
    update_sheet(workbook, "_資産推移データ(自動入力)", "../csv/portfolio/portfolio_all.csv")
    update_sheet(workbook, "_預金・現金・暗号資産", "../csv/portfolio/portfolio_det_depo.csv")
    update_sheet(workbook, "_株式（現物）", "../csv/portfolio/portfolio_det_eq.csv")
    update_sheet(workbook, "_投資信託", "../csv/portfolio/portfolio_det_mf.csv")
    update_sheet(workbook, "_年金", "../csv/portfolio/portfolio_det_pns.csv")


if __name__ == "__main__":
    main()