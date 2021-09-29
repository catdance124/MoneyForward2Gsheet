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

def main():
    config_ini = configparser.ConfigParser()
    config_ini.read('config.ini', encoding='utf-8')
    spreadsheet_key = config_ini.get('SPREAD_SHEET', 'Key')
    spreadsheet_worksheet_name = config_ini.get('SPREAD_SHEET', 'Worksheet_name')
    
    workbook = connect_gspread(json_path="client_secret.json", spreadsheet_key=spreadsheet_key)
    workbook.values_update(
        spreadsheet_worksheet_name,
        params={'valueInputOption': 'USER_ENTERED'},
        body={'values': list(csv.reader(open("../csv/all.csv", encoding='shift-jis')))}
    )


if __name__ == "__main__":
    main()