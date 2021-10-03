import configparser
import csv
import gspread
from oauth2client.service_account import ServiceAccountCredentials


def connect_gspread(json_path, spreadsheet_key):
    scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(json_path, scope)
    gc = gspread.authorize(credentials)
    workbook = gc.open_by_key(spreadsheet_key)
    return workbook

def update_sheet(workbook, worksheet_name, csv_path):
    if not worksheet_name in [worksheet.title for worksheet in workbook.worksheets()]:
        workbook.add_worksheet(title=worksheet_name, rows=50, cols=50)
    workbook.values_update(
        worksheet_name,
        params={'valueInputOption': 'USER_ENTERED'},
        body={'values': list(csv.reader(open(csv_path, encoding='shift-jis')))}
    )

def main():
    config_ini = configparser.ConfigParser()
    config_ini.read('config.ini', encoding='utf-8')
    spreadsheet_key = config_ini.get('SPREAD_SHEET', 'Key')
    
    workbook = connect_gspread(json_path="client_secret.json", spreadsheet_key=spreadsheet_key)
    update_sheet(workbook, "_資産推移データ(自動入力)", "../csv/all.csv")
    update_sheet(workbook, "_預金・現金・暗号資産", "../csv/portfolio/portfolio_det_depo.csv")
    update_sheet(workbook, "_株式（現物）", "../csv/portfolio/portfolio_det_eq.csv")
    update_sheet(workbook, "_投資信託", "../csv/portfolio/portfolio_det_mf.csv")
    update_sheet(workbook, "_年金", "../csv/portfolio/portfolio_det_pns.csv")


if __name__ == "__main__":
    main()